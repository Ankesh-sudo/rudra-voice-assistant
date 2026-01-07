from loguru import logger

from core.input.input_validator import InputValidator
from core.storage.mysql import verify_connection
from core.input_controller import InputController

from core.nlp.normalizer import normalize_text
from core.nlp.intent import Intent
from core.skills.basic import handle as basic_handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
from core.intelligence.intent_scorer import score_intents, pick_best_intent
from core.intelligence.confidence_refiner import refine_confidence
from core.actions.action_executor import ActionExecutor


# ===============================
# Day 16 — Global confidence gate
# ===============================
INTENT_CONFIDENCE_THRESHOLD = 0.65


# ===============================
# Day 17.1 — Clarification pool
# ===============================
CLARIFICATION_MESSAGES = [
    "I’m not sure what you meant. Can you rephrase?",
    "Could you explain that a bit more?",
    "I didn’t fully get that. What would you like to do?",
    "That’s unclear to me—can you try again?",
]


# ===============================
# Day 17.3 — Cooldown thresholds
# ===============================
COOLDOWN_THRESHOLD = 2
HELP_THRESHOLD = 3

HELP_MESSAGE = (
    "Let’s slow down. You can say things like:\n"
    "- open browser\n"
    "- search Python decorators\n"
    "- open downloads folder"
)


IDLE = "idle"
ACTIVE = "active"
WAITING = "waiting"


def has_reference(tokens: list[str]) -> bool:
    return "__REF__" in tokens or "__REPEAT__" in tokens


def is_pronoun_only(tokens: list[str]) -> bool:
    return "__REF__" in tokens or "__REPEAT__" in tokens


def is_short_followup(tokens: list[str]) -> bool:
    """Day 17.5 — short but meaningful follow-up"""
    return 1 <= len(tokens) <= 3 and not is_pronoun_only(tokens)


class Assistant:
    def __init__(self):
        self.input = InputController()
        self.name = "Rudra"
        self.running = True
        self.ctx = ShortTermContext()

        self.input_validator = InputValidator()
        self.state = IDLE
        self.silence_count = 0
        self.action_executor = ActionExecutor()
        self.expecting_followup = False

        # Day 17 state
        self.clarify_index = 0
        self.failure_count = 0
        self.last_was_clarification = False

    def next_clarification(self) -> str:
        msg = CLARIFICATION_MESSAGES[self.clarify_index]
        self.clarify_index = (self.clarify_index + 1) % len(CLARIFICATION_MESSAGES)
        return msg

    def run(self):
        logger.info("Assistant initialized: {}", self.name)

        ok, msg = verify_connection()
        logger.info("MySQL connection OK: {}", msg) if ok else logger.error(msg)

        logger.info("Day 17.5 started — Smart follow-up recovery enabled")

        while self.running:
            raw_text = self.input.read()

            if not raw_text:
                if self.state in (ACTIVE, WAITING):
                    self.silence_count += 1
                    if self.silence_count == 1:
                        print("Rudra > I'm listening.")
                        self.state = WAITING
                        continue
                    if self.silence_count >= 2:
                        print("Rudra > Going to sleep.")
                        self.state = IDLE
                        self.silence_count = 0
                continue

            self.silence_count = 0
            self.state = ACTIVE

            validation = self.input_validator.validate(raw_text)
            if not validation["valid"]:
                self.input_validator.mark_rejected()
                print("Rudra > I didn’t understand. Please repeat.")
                continue

            clean_text = validation["clean_text"]
            tokens = normalize_text(clean_text)

            # =================================================
            # 🔒 Day 17.4 — Pronoun-only block
            # =================================================
            if self.last_was_clarification and is_pronoun_only(tokens):
                print("Rudra > Please say a full command so I can help you.")
                continue

            scores = {}
            confidence = 0.0
            intent = Intent.UNKNOWN
            replay_args = None

            # =================================================
            # 🔁 Context replay (unchanged)
            # =================================================
            if has_reference(tokens):
                if self.ctx.has_last_action():
                    intent = Intent(self.ctx.last_intent)
                    clean_text = self.ctx.last_text
                    replay_args = self.ctx.last_entities
                    confidence = 1.0
                else:
                    print("Rudra > I’m not sure what you’re referring to.")
                    continue

            # =================================================
            # 🧠 Day 17.5 — SMART FOLLOW-UP RECOVERY
            # =================================================
            elif (
                self.last_was_clarification
                and is_short_followup(tokens)
                and self.ctx.has_last_action()
            ):
                intent = Intent(self.ctx.last_intent)
                confidence = 0.75  # boosted, not forced
                logger.info(
                    "[DAY 17.5] Recovering intent={} from short follow-up tokens={}",
                    intent.value, tokens
                )

            else:
                scores = score_intents(tokens)
                intent, confidence = pick_best_intent(scores, tokens)
                confidence = refine_confidence(
                    confidence, tokens, intent.value, self.ctx.last_intent
                )

            logger.debug(
                "Tokens={} | Intent={} | Confidence={:.2f}",
                tokens, intent.value, confidence
            )

            # =================================================
            # 🔒 Confidence gate
            # =================================================
            if confidence < INTENT_CONFIDENCE_THRESHOLD:
                self.failure_count += 1
                self.last_was_clarification = True

                msg = (
                    HELP_MESSAGE
                    if self.failure_count >= HELP_THRESHOLD
                    else self.next_clarification()
                )

                print(f"Rudra > {msg}")
                continue

            if intent == Intent.UNKNOWN:
                self.failure_count += 1
                self.last_was_clarification = True
                print(f"Rudra > {self.next_clarification()}")
                continue

            # -------- MEMORY --------
            save_message("user", clean_text, intent.value)

            # -------- EXECUTION --------
            result = None
            if intent in (Intent.GREETING, Intent.HELP):
                response = basic_handle(intent, clean_text)

            elif intent == Intent.EXIT:
                print("Rudra > Goodbye!")
                save_message("assistant", "Goodbye!", intent.value)
                break

            else:
                result = self.action_executor.execute(
                    intent, clean_text, confidence, replay_args=replay_args
                )
                response = result.get("message", "Done.")

            print(f"Rudra > {response}")
            save_message("assistant", response, intent.value)

            # -------- SUCCESS RESET --------
            if result and result.get("success"):
                self.failure_count = 0
                self.last_was_clarification = False
                self.ctx.update(intent.value, text=clean_text, entities=result.get("args"))
            else:
                self.ctx.update(intent.value)
