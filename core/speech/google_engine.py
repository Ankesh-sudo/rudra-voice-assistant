import speech_recognition as sr
from loguru import logger

from core.control.global_interrupt import GLOBAL_INTERRUPT


class GoogleSpeechEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(device_index=9)
        logger.info("Google Speech Engine initialized")

    def listen_once(self) -> str:
        # If interrupt already active, do not listen
        if GLOBAL_INTERRUPT.is_triggered():
            logger.warning("Listen aborted due to global interrupt")
            return ""

        with self.microphone as source:
            logger.info("Listening (Google)...")
            audio = self.recognizer.listen(source)

        # Check interrupt again after capture
        if GLOBAL_INTERRUPT.is_triggered():
            logger.warning("Audio captured but interrupt triggered — discarding")
            return ""

        try:
            text = self.recognizer.recognize_google(audio)

            # Final interrupt check before returning text
            if GLOBAL_INTERRUPT.is_triggered():
                logger.warning("Interrupt triggered before returning recognized text")
                return ""

            logger.info("Google heard: {}", text)
            return text

        except Exception as e:
            logger.error("Google Speech Recognition failed: {}", e)
            return ""
