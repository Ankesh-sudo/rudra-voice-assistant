import os
import re
from typing import Optional

from core.nlp.intent import Intent
from core.system.path_resolver import resolve_base_path, resolve_file_path
from core.system.file_reader import read_text_file


# ---------------------------
# Public entry point
# ---------------------------

def handle(intent: Intent, raw_text: str) -> str:
    text = normalize_text(raw_text.lower().strip())

    if intent == Intent.LIST_FILES:
        return _handle_list_files(text)

    if intent == Intent.READ_FILE:
        return _handle_read_file(text)

    return "I can't do that."


# ---------------------------
# LIST FILES
# ---------------------------

def _handle_list_files(text: str) -> str:
    base_dir = resolve_base_path(text)

    if not base_dir or not os.path.isdir(base_dir):
        return "I can't access that location."

    try:
        entries = sorted(os.listdir(base_dir))
    except Exception:
        return "I couldn't list files there."

    if not entries:
        return "That folder is empty."

    entries = entries[:20]

    files = []
    folders = []

    for item in entries:
        full_path = os.path.join(base_dir, item)
        if os.path.isdir(full_path):
            folders.append(item + "/")
        else:
            files.append(item)

    parts = []
    if folders:
        parts.append("Folders: " + ", ".join(folders))
    if files:
        parts.append("Files: " + ", ".join(files))

    return " | ".join(parts)


# ---------------------------
# READ FILE
# ---------------------------

def _handle_read_file(text: str) -> str:
    filename = _extract_filename(text)
    if not filename:
        return "Please tell me the file name."

    base_dir = resolve_base_path(text)
    if not base_dir:
        return "I can't access that location."

    path = resolve_file_path(filename, base_dir)
    if not path:
        return "I couldn't find that file."

    content = read_text_file(path)
    if content is None:
        return "That file cannot be read safely."

    content = content.strip()
    if not content:
        return "The file is empty."

    MAX_CHARS = 800
    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + "..."

    return f"Here is the content of {filename}:\n{content}"


# ---------------------------
# Helpers
# ---------------------------

def normalize_text(text: str) -> str:
    """
    Normalizes spoken filenames:
    'notes dot txt' → 'notes.txt'
    """
    return (
        text.replace(" dot ", ".")
            .replace(" dot", ".")
            .replace(" txt", ".txt")
            .replace(" pdf", ".pdf")
            .replace(" md", ".md")
            .replace(" log", ".log")
            .strip()
    )


def _extract_filename(text: str) -> Optional[str]:
    match = re.search(r"\b([\w\-]+\.(txt|md|log|pdf))\b", text)
    if match:
        return match.group(1)
    return None
