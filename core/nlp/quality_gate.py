SYSTEM_WORDS = {"exit", "quit", "help", "repeat", "again"}
STOPWORDS = {
    "the", "is", "am", "are", "was", "were",
    "to", "of", "and", "a", "an"
}
def is_input_valid(text: str) -> bool:
    if not text:
        return False

    words = text.split()

    # allow system commands
    if len(words) == 1 and words[0] in SYSTEM_WORDS:
        return True

    if len(words) < 2:
        return False

    if len(text) < 5:
        return False

    meaningful = [w for w in words if w not in STOPWORDS]
    return len(meaningful) > 0
