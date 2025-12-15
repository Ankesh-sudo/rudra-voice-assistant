from typing import Dict, List
from core.nlp.intent import Intent

# Keyword evidence per intent (language-agnostic at core level)
INTENT_KEYWORDS: Dict[Intent, List[str]] = {
    Intent.GREETING: ["hi", "hello", "hey"],
    Intent.HELP: ["help", "commands"],
    Intent.EXIT: ["exit", "quit", "bye"],
}

def score_intents(tokens: List[str]) -> Dict[Intent, int]:
    scores: Dict[Intent, int] = {i: 0 for i in Intent}

    for intent, kws in INTENT_KEYWORDS.items():
        for t in tokens:
            if t in kws:
                scores[intent] += 1

    return scores

def pick_best_intent(scores: Dict[Intent, int]) -> Intent:
    # choose highest score; tie-breaker handled by order
    best = max(scores.items(), key=lambda x: x[1])
    if best[1] == 0:
        return Intent.UNKNOWN
    return best[0]
