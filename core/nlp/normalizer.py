import re

FILLER_WORDS = [
    "um", "uh", "hmm", "please", "hey",
     "okay", "ok", "ya", "yeah"
]

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)

    words = text.split()
    words = [w for w in words if w not in FILLER_WORDS]

    return " ".join(words).strip()
