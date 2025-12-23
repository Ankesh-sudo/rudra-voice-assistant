from typing import Dict, List
from core.nlp.intent import Intent

# Keyword evidence per intent
INTENT_KEYWORDS: Dict[Intent, List[str]] = {
    # Core
    Intent.GREETING: ["hi", "hello", "hey"],
    Intent.HELP: ["help", "commands"],
    Intent.EXIT: ["exit", "quit", "bye"],

    # Notes
    Intent.NOTE_CREATE: ["note", "save", "write", "take"],
    Intent.NOTE_READ: ["read", "show", "list"],

    # --------------------
    # Day 10 – System actions
    # --------------------
    Intent.OPEN_BROWSER: ["browser", "chrome", "firefox", "internet"],
    Intent.OPEN_TERMINAL: ["terminal", "console", "shell"],
    Intent.OPEN_FILE_MANAGER: ["files", "file", "folder", "directory"],
}


def score_intents(tokens: List[str]) -> Dict[Intent, int]:
    """
    Score intents based on keyword matches.
    """
    scores: Dict[Intent, int] = {i: 0 for i in Intent}

    for intent, keywords in INTENT_KEYWORDS.items():
        for token in tokens:
            if token in keywords:
                scores[intent] += 1

    # Special handling for action verbs
    if "open" in tokens:
        for intent in (
            Intent.OPEN_BROWSER,
            Intent.OPEN_TERMINAL,
            Intent.OPEN_FILE_MANAGER,
        ):
            if scores[intent] > 0:
                scores[intent] += 1  # boost system intent

    return scores


def pick_best_intent(scores: Dict[Intent, int], tokens: List[str]):
    """
    Pick intent with highest score.
    """
    if not scores:
        return Intent.UNKNOWN, 0.0

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score == 0:
        return Intent.UNKNOWN, 0.0
    
    if best_intent == Intent.EXIT:
        return Intent.EXIT, 1.0

    # Normalize confidence (simple, deterministic)
    confidence = min(1.0, best_score / max(1, len(tokens)))

    return best_intent, confidence
