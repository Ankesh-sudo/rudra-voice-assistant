import time
from loguru import logger
from core.speech.google_engine import GoogleSpeechEngine
from core.speech.wake_word import contains_wake_word


class InputController:
    def __init__(self):
        self.speech = GoogleSpeechEngine()
        self.active = False
        self.last_active_time = 0
        self.ACTIVE_TIMEOUT = 45

    def read(self) -> str:
        now = time.time()

        # Only ask for ENTER if assistant is sleeping
        if not self.active:
            input("Press ENTER and speak...")

        text = self.speech.listen_once()
        logger.debug("Raw speech: {}", text)

        if not text:
            return ""

        now = time.time()

        # If already active, accept speech directly
        if self.active and (now - self.last_active_time) < self.ACTIVE_TIMEOUT:
            self.last_active_time = now
            return text

        # Wake-word detection
        if contains_wake_word(text):
            self.active = True
            self.last_active_time = now

            clean_text = text.lower().replace("rudra", "").strip()

            if not clean_text:
                print("Rudra > Yes?")
                return ""

            return clean_text

        # No wake word and not active
        print("Rudra > (going to sleep)")
        self.active = False
        return ""
