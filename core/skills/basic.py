from loguru import logger
from core.nlp.intent import Intent
from core.system.app_registry import AppRegistry

# ✅ SINGLE GLOBAL REGISTRY — ONLY ONE
REGISTRY = AppRegistry()


def handle(intent: Intent, text: str) -> str:

    if intent == Intent.OPEN_BROWSER:
        logger.debug("Handling intent: OPEN_BROWSER")
        return "Opening browser." if REGISTRY.execute("open_browser") else "I couldn't open the browser."

    if intent == Intent.OPEN_TERMINAL:
        logger.debug("Handling intent: OPEN_TERMINAL")
        return "Opening terminal." if REGISTRY.execute("open_terminal") else "I couldn't open the terminal."

    if intent == Intent.OPEN_FILE_MANAGER:
        logger.debug("Handling intent: OPEN_FILE_MANAGER")
        return "Opening file manager." if REGISTRY.execute("open_file_manager") else "I couldn't open the file manager."

    if intent == Intent.GREETING:
        return "Hello. I am Rudra."

    if intent == Intent.HELP:
        return "You can ask me to open browser, terminal, or file manager."

    if intent == Intent.EXIT:
        return "Goodbye."

    return "I don't know how to do that yet."
