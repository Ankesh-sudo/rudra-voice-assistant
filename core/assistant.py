from loguru import logger
from core.nlp.quality_gate import is_input_valid
from core.storage.mysql import verify_connection
from core.input_controller import InputController
from core.nlp.tokenizer import tokenize
from core.nlp.intent import Intent
from core.nlp.normalizer import normalize_text
from core.skills.basic import handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
from core.intelligence.intent_scorer import score_intents, pick_best_intent


class Assistant:
    def __init__(self):
        self.input = InputController()
        self.name = "Rudra"
        self.running = True
        self.ctx = ShortTermContext()

    def run(self):
        logger.info("Assistant initialized: {}", self.name)

        ok, msg = verify_connection()
        if ok:
            logger.info("MySQL connection OK: {}", msg)
        else:
            logger.error("MySQL connection FAILED: {}", msg)

        logger.info("Day 8 started. Input control enabled.")

        while self.running:
            raw_text = self.input.read()
            if not raw_text:
                continue

            normalized = normalize_text(raw_text)

            # QUALITY GATE
            if not is_input_valid(normalized):
                logger.debug(
                    "Rejected input | raw='{}' | normalized='{}' | reason=quality_gate",
                    raw_text, normalized
                )
                print("Rudra > I didn't catch that clearly.")
                continue

            tokens = tokenize(normalized)

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

            logger.debug(
                "Tokens={} | Scores={} | Intent={} | Confidence={:.2f}",
                tokens, scores, intent.value, confidence
            )

            # CONFIDENCE GATE (STRICT)
            if confidence < 0.60:
                logger.debug(
                    "Rejected input | tokens={} | intent={} | confidence={:.2f}",
                    tokens, intent.value, confidence
                )
                print("Rudra > Please say that again.")
                continue

            save_message("user", normalized, intent.value)

            response = handle(intent, normalized)
            print(f"Rudra > {response}")

            save_message("assistant", response, intent.value)

            self.ctx.update(intent.value)

            if intent == Intent.EXIT:
                self.running = False
