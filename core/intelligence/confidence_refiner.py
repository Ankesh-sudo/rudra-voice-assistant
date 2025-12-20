# core/intelligence/confidence_refiner.py

STRONG_VERBS = {"open", "save", "read", "exit", "play", "stop"}

def refine_confidence(base_confidence: float, tokens: list[str], intent: str, last_intent: str | None) -> float:
    confidence = base_confidence

    # Keyword boost
    if any(t in STRONG_VERBS for t in tokens):
        confidence += 0.15

    # Length penalty (except greetings/help)
    if len(tokens) <= 2 and intent not in ("greeting", "help"):
        confidence -= 0.10

    # Context boost
    if last_intent and intent == last_intent:
        confidence += 0.20

    # Clamp
    if confidence < 0.0:
        confidence = 0.0
    if confidence > 1.0:
        confidence = 1.0

    return confidence
