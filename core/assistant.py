from loguru import logger
from core.storage.mysql import verify_connection
from core.input.text_input import read_text
from core.nlp.tokenizer import tokenize
from core.nlp.intent import Intent
from core.skills.basic import handle
from core.context.short_term import ShortTermContext
from core.intelligence.intent_scorer import score_intents, pick_best_intent

class Assistant:
    def __init__(self):
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

        logger.info("Day 3 started. Intent scoring + context enabled.")

        while self.running:
            text = read_text()
            tokens = tokenize(text)

            # Simple follow-up handling
            if tokens in (["again"], ["repeat"]):
                if self.ctx.last_intent:
                    intent = Intent(self.ctx.last_intent)
                else:
                    intent = Intent.UNKNOWN
            else:
                scores = score_intents(tokens)
                intent = pick_best_intent(scores)

            response = handle(intent)
            print(f"Rudra > {response}")

            self.ctx.update(intent.value)

            if intent == Intent.EXIT:
                self.running = False

        logger.info("Day 3 complete.")
