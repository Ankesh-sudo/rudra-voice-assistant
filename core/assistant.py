from loguru import logger

from core.input.input_validator import InputValidator
from core.storage.mysql import verify_connection
from core.input_controller import InputController
from core.nlp.tokenizer import tokenize
from core.nlp.intent import Intent
from core.skills.basic import handle as basic_handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
from core.intelligence.intent_scorer import score_intents, pick_best_intent
from core.intelligence.confidence_refiner import refine_confidence

# Day 12
from core.actions.action_executor import ActionExecutor


# Day 9.3 – Listening states
IDLE = "idle"
ACTIVE = "active"
WAITING = "waiting"


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

        # Day 12 – Action executor
        self.action_executor = ActionExecutor()

        # Day 13.3 – follow-up hint (kept, but safe)
        self.expecting_followup = False

    def run(self):
        logger.info("Assistant initialized: {}", self.name)

        ok, msg = verify_connection()
        if ok:
            logger.info("MySQL connection OK: {}", msg)
        else:
            logger.error("MySQL connection FAILED: {}", msg)

        logger.info("Day 14.1 started — UNKNOWN intent execution blocked")

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

            # Reset silence on speech
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

            # -------- TOKENIZATION --------
            tokens = tokenize(clean_text)

            scores = {}
            confidence = 0.0

            # -------- INTENT DETECTION --------
            scores = score_intents(tokens)
            intent, confidence = pick_best_intent(scores, tokens)

            confidence = refine_confidence(
                confidence,
                tokens,
                intent.value,
                self.ctx.last_intent
            )

            logger.debug(
                "Tokens={} | Scores={} | Intent={} | Confidence={:.2f}",
                tokens, scores, intent.value, confidence
            )

            # =================================================
            # 🔒 Day 14.1 — HARD SAFETY BLOCK (CRITICAL)
            # =================================================
            if intent == Intent.UNKNOWN:
                percent = int(confidence * 100)
                print(f"Rudra > I'm not confident enough ({percent}%). Please rephrase.")
                logger.warning(
                    "[DAY 14.1 BLOCK] UNKNOWN intent blocked | tokens={} | confidence={:.2f}",
                    tokens, confidence
                )
                self.expecting_followup = False
                continue
            # =================================================

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
                    intent, clean_text, confidence
                )

                if not result.get("success", False):
                    response = result.get("message", "I couldn't do that.")
                else:
                    response = result.get("message", "Done.")

            print(f"Rudra > {response}")

            save_message("assistant", response, intent.value)
            self.ctx.update(intent.value)

            # -------- FOLLOW-UP EXPECTATION (SAFE) --------
            if result and result.get("executed", False) and result.get("success", False):
                self.expecting_followup = len(clean_text.split()) <= 4
            else:
                self.expecting_followup = False
