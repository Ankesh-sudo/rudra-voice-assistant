

from typing import Dict
from core.nlp.normalizer import normalize_text


class InputValidator:
    def __init__(self):
        self._last_input = None

    def validate(self, raw_text: str) -> Dict[str, str | bool]:
        """
        Validate input text before intent processing.
        """
        clean_text = normalize_text(raw_text)

        # Empty after normalization
        if not clean_text:
            return {
                "valid": False,
                "clean_text": "",
                "reason": "empty"
            }

        # Too short
        if len(clean_text) < 3:
            return {
                "valid": False,
                "clean_text": clean_text,
                "reason": "too_short"
            }

        words = clean_text.split()

        # Too few words
        if len(words) < 2:
            return {
                "valid": False,
                "clean_text": clean_text,
                "reason": "too_few_words"
            }


        if self._last_input and clean_text in self._last_input:
            return {
                "valid": False,
                "clean_text": clean_text,
                "reason": "repeat"
            }

        self._last_input = clean_text


        return {
            "valid": True,
            "clean_text": clean_text,
            "reason": None
        }
