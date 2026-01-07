from loguru import logger

from core.input.input_validator import InputValidator
from core.storage.mysql import verify_connection
from core.input_controller import InputController

# Day 14.2 — Normalizer
from core.nlp.normalizer import normalize_text

from core.nlp.intent import Intent
from core.skills.basic import handle as basic_handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
from core.intelligence.intent_scorer import score_intents, pick_best_intent
from core.intelligence.confidence_refiner import refine_confidence

# Day 12 / Day 14.4
from core.actions.action_executor import ActionExecutor


# ===============================
# Day 16 — Global confidence gate
# ===============================
INTENT_CONFIDENCE_THRESHOLD = 0.65


# Day 9.3 – Listening states
IDLE = "idle"
ACTIVE = "active"
WAITING = "waiting"


def has_reference(tokens: list[str]) -> bool:
    """Detect reference-based commands like 'it', 'again'."""
    return "__REF__" in tokens or "__REPEAT__" in tokens


class Assistant:
    def __init__(self):
        self.input = InputController()
        self.name = "Rudra"
        self.running = True
        self.ctx = ShortTermContext()

        # Day 9.1 – Input intelligence gate
        self.input_validator = InputValidator()

        # Day 9.3 – Active listening state
        self.state = IDLE
        self.silence_count = 0

        # Day 12 / Day 14.4 – Action executor
        self.action_executor = ActionExecutor()

        # Day 13.3 – follow-up hint (safe)
        self.expecting_followup = False

    def run(self):
        logger.info("Assistant initialized: {}", self.name)

        ok, msg = verify_connection()
        if ok:
            logger.info("MySQL connection OK: {}", msg)
        else:
            logger.error("MySQL connection FAILED: {}", msg)

        logger.info("Day 16 started — Intent confidence gating enabled")

        while self.running:
            raw_text = self.input.read()

            # -------- SILENCE HANDLING (Day 9.3) --------
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
                continue
            # --------------------------------------------

            self.silence_count = 0
            self.state = ACTIVE

            # -------- INPUT VALIDATION --------
            validation = self.input_validator.validate(raw_text)

            logger.debug("[INPUT] raw='{}'", raw_text)
            logger.debug("[INPUT] clean='{}'", validation.get("clean_text"))
            logger.debug("[VALIDATION] {}", validation)

            if not validation["valid"]:
                self.input_validator.mark_rejected()
                print("Rudra > I didn’t understand. Please repeat.")
                continue
            # ---------------------------------

            clean_text = validation["clean_text"]

            # -------- PHRASE NORMALIZATION (Day 14.2) --------
            tokens = normalize_text(clean_text)
            # -----------------------------------------------

            scores = {}
            confidence = 0.0
            intent = Intent.UNKNOWN
            replay_args = None

            # =================================================
            # 🔁 Day 14.3 + 14.4 — CONTEXT REFERENCE RESOLUTION
            # =================================================
            if has_reference(tokens):
                if self.ctx.has_last_action():
                    intent = Intent(self.ctx.last_intent)
                    clean_text = self.ctx.last_text
                    replay_args = self.ctx.last_entities
                    confidence = 1.0

                    logger.info(
                        "[DAY 14.4] Replaying last action | intent={} | text='{}' | args={}",
                        intent.value, clean_text, replay_args
                    )
                else:
                    print("Rudra > I’m not sure what you’re referring to.")
                    logger.warning("[DAY 14 BLOCK] Reference used with no context")
                    continue
            else:
                # -------- NORMAL INTENT DETECTION --------
                scores = score_intents(tokens)
                intent, confidence = pick_best_intent(scores, tokens)

                confidence = refine_confidence(
                    confidence,
                    tokens,
                    intent.value,
                    self.ctx.last_intent
                )
            # =================================================

            logger.debug(
                "Tokens={} | Scores={} | Intent={} | Confidence={:.2f}",
                tokens, scores, intent.value, confidence
            )

            # =================================================
            # 🔒 Day 16 — HARD CONFIDENCE GATE (Assistant-level)
            # =================================================
            if confidence < INTENT_CONFIDENCE_THRESHOLD:
                percent = int(confidence * 100)
                print(f"Rudra > I'm not confident enough ({percent}%). Can you rephrase?")
                logger.warning(
                    "[DAY 16 BLOCK] Low confidence intent blocked | intent={} | tokens={} | confidence={:.2f}",
                    intent.value, tokens, confidence
                )
                self.expecting_followup = False
                continue
            # =================================================

            # =================================================
            # 🔒 Day 14.1 — UNKNOWN INTENT BLOCK (STILL VALID)
            # =================================================
            if intent == Intent.UNKNOWN:
                percent = int(confidence * 100)
                print(f"Rudra > I'm not confident enough ({percent}%). Please rephrase.")
                logger.warning(
                    "[DAY 14 BLOCK] UNKNOWN intent blocked | tokens={} | confidence={:.2f}",
                    tokens, confidence
                )
                self.expecting_followup = False
                continue
            # =================================================

            # -------- MEMORY WRITE (SAFE ZONE) --------
            save_message("user", clean_text, intent.value)

            # -------- EXECUTION --------
            response = None
            result = None

            if intent in (Intent.GREETING, Intent.HELP):
                response = basic_handle(intent, clean_text)

            elif intent == Intent.EXIT:
                response = "Goodbye!"
                print(f"Rudra > {response}")
                save_message("assistant", response, intent.value)
                self.running = False
                break

            else:
                result = self.action_executor.execute(
                    intent,
                    clean_text,
                    confidence,
                    replay_args=replay_args
                )

                if not result.get("success", False):
                    response = result.get("message", "I couldn't do that.")
                else:
                    response = result.get("message", "Done.")

            print(f"Rudra > {response}")

            save_message("assistant", response, intent.value)

            # =================================================
            # ✅ Update context ONLY after successful execution
            # =================================================
            if result and result.get("executed", False) and result.get("success", False):
                self.ctx.update(
                    intent.value,
                    text=clean_text,
                    entities=result.get("args")
                )
            else:
                self.ctx.update(intent.value)
            # =================================================

            # -------- FOLLOW-UP EXPECTATION (SAFE) --------
            if result and result.get("executed", False) and result.get("success", False):
                self.expecting_followup = len(clean_text.split()) <= 4
            else:
                self.expecting_followup = False
