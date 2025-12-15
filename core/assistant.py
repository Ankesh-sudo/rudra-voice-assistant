from loguru import logger
from core.storage.mysql import verify_connection
from core.input.text_input import read_text
from core.nlp.tokenizer import tokenize
from core.nlp.intent import Intent
from core.nlp.normalizer import normalize
from core.skills.basic import handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
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

        logger.info("Day 4 started. Long-term memory enabled.")

        while self.running:
            user_text = read_text()
            user_text = normalize(user_text) 
            tokens = tokenize(user_text)

            # Follow-up handling
            if tokens in (["again"], ["repeat"]):
                if self.ctx.last_intent:
                    intent = Intent(self.ctx.last_intent)
                else:
                    intent = Intent.UNKNOWN
            else:
                scores = score_intents(tokens)
                intent = pick_best_intent(scores, tokens)


            # Save user message
            save_message("user", user_text, intent.value)

            response = handle(intent, user_text)
            print(f"Rudra > {response}")

            # Save assistant response
            save_message("assistant", response, intent.value)

            # Update short-term context
            self.ctx.update(intent.value)

            if intent == Intent.EXIT:
                self.running = False

        logger.info("Day 4 complete.")
