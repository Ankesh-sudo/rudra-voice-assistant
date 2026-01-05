from typing import Dict, List
from core.nlp.intent import Intent


# -------------------------------------------------
# Day 14.4 — Verb aliases (minimal & deterministic)
# -------------------------------------------------
VERB_ALIASES: Dict[str, Intent] = {
    # Search intent
    "search": Intent.SEARCH_WEB,
    "find": Intent.SEARCH_WEB,
    "lookup": Intent.SEARCH_WEB,
    "look": Intent.SEARCH_WEB,

    # Open intent (browser/system)
    "open": Intent.OPEN_BROWSER,
    "launch": Intent.OPEN_BROWSER,
    "start": Intent.OPEN_BROWSER,
}


# -------------------------------------------------
# Keyword evidence per intent
# -------------------------------------------------
INTENT_KEYWORDS: Dict[Intent, List[str]] = {
    # Core
    Intent.GREETING: ["hi", "hello", "hey"],
    Intent.HELP: ["help", "commands"],
    Intent.EXIT: ["exit", "quit", "bye"],

    # Notes
    Intent.NOTE_CREATE: ["note", "save", "write", "take"],
    Intent.NOTE_READ: ["read", "show", "list"],

    # --------------------
    # System actions
    # --------------------
    Intent.OPEN_BROWSER: [
        "browser",
        "chrome",
        "firefox",
        "internet",
        "youtube",
        "google",
        "github",
        "website",
        "site",
    ],

    Intent.OPEN_TERMINAL: [
        "terminal",
        "console",
        "shell",
    ],

    Intent.OPEN_FILE_MANAGER: [
        "files",
        "file",
        "folder",
        "directory",
        "downloads",
        "download",
        "desktop",
        "documents",
    ],

    # --------------------
    # Day 14.4 — Search intent keywords
    # --------------------
    Intent.SEARCH_WEB: [
        "search",
        "find",
        "lookup",
        "query",
    ],
}


def score_intents(tokens: List[str]) -> Dict[Intent, int]:
    """
    Score intents based on keyword + verb evidence.
    Rule-based, deterministic (Day 9–14 safe).
    """
    scores: Dict[Intent, int] = {i: 0 for i in Intent}

    # Keyword matching
    for intent, keywords in INTENT_KEYWORDS.items():
        for token in tokens:
            if token in keywords:
                scores[intent] += 1

    # -------------------------------------------------
    # Day 14.4 — Verb alias boosting
    # -------------------------------------------------
    for token in tokens:
        alias_intent = VERB_ALIASES.get(token)
        if alias_intent:
            scores[alias_intent] += 1

    # -------------------------------------------------
    # Action verb boost (existing behavior preserved)
    # -------------------------------------------------
    if "open" in tokens or "launch" in tokens or "start" in tokens:
        for intent in (
            Intent.OPEN_BROWSER,
            Intent.OPEN_TERMINAL,
            Intent.OPEN_FILE_MANAGER,
        ):
            if scores[intent] > 0:
                scores[intent] += 1

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

    # EXIT is always confident
    if best_intent == Intent.EXIT:
        return Intent.EXIT, 1.0

    # Normalize confidence (deterministic)
    confidence = min(1.0, best_score / max(1, len(tokens)))

    return best_intent, confidence
