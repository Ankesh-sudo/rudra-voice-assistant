from loguru import logger

from core.input.input_validator import InputValidator
from core.storage.mysql import verify_connection
from core.input_controller import InputController
from core.nlp.tokenizer import tokenize
from core.nlp.intent import Intent
from core.skills.basic import handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
from core.intelligence.intent_scorer import score_intents, pick_best_intent
from core.intelligence.confidence_refiner import refine_confidence


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

    def run(self):
        logger.info("Assistant initialized: {}", self.name)

        ok, msg = verify_connection()
        if ok:
            logger.info("MySQL connection OK: {}", msg)
        else:
            logger.error("MySQL connection FAILED: {}", msg)

        logger.info("Day 9.3 started. Active listening enabled.")

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

            # -------- INPUT VALIDATION GATE --------
            validation = self.input_validator.validate(raw_text)

            logger.debug("[INPUT] raw='{}'", raw_text)
            logger.debug("[INPUT] clean='{}'", validation.get("clean_text"))
            logger.debug("[VALIDATION] {}", validation)

            if not validation["valid"]:
                print("Rudra > I didn’t understand. Please repeat.")
                continue
            # --------------------------------------

            clean_text = validation["clean_text"]

            # Tokenization
            tokens = tokenize(clean_text)

            scores = {}
            confidence = 0.0

            # FOLLOW-UP HANDLING
            if tokens in (["again"], ["repeat"]):
                if self.ctx.last_intent:
                    intent = Intent(self.ctx.last_intent)
                    confidence = 1.0
                else:
                    intent = Intent.UNKNOWN
                    confidence = 0.0
            else:
                scores = score_intents(tokens)
                intent, confidence = pick_best_intent(scores, tokens)

                # Day 9.2 – Confidence refinement
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
            if intent == Intent.UNKNOWN:
                print("Rudra > I don’t know how to do that yet.")
                continue
            # CONFIDENCE GATE
            if confidence < 0.60:
                logger.debug(
                    "Rejected by confidence gate | tokens={} | intent={} | confidence={:.2f}",
                    tokens, intent.value, confidence
                )
                print("Rudra > Please say that again.")
                continue

            # Save user message
            save_message("user", clean_text, intent.value)

            # Execute skill
            response = handle(intent, clean_text)
            print(f"Rudra > {response}")

            # Save assistant message
            save_message("assistant", response, intent.value)

            # Update short-term context
            self.ctx.update(intent.value)

            if intent == Intent.EXIT:
                self.running = False
