COMMON_FIXES = {
    "read not": "read note",
    "save not": "save note",
    "steve note": "save note",
    "that": "",
}

def normalize(text: str) -> str:
    t = text.lower()
    for wrong, right in COMMON_FIXES.items():
        t = t.replace(wrong, right)
    return t.strip()
