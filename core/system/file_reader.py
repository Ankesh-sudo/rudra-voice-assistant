import os
from typing import Optional

from core.system.config import HOME_DIR

# Safety limits
ALLOWED_EXTENSIONS = {".txt", ".md", ".log"}
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB


def is_safe_file(path: str) -> bool:
    """
    Validate file safety:
    - inside HOME_DIR
    - allowed extension
    - within size limit
    """
    if not path:
        return False

    # Must be absolute and inside HOME
    path = os.path.abspath(path)
    if not path.startswith(HOME_DIR):
        return False

    if not os.path.isfile(path):
        return False

    _, ext = os.path.splitext(path)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return False

    try:
        size = os.path.getsize(path)
        if size > MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False

    return True


def read_text_file(path: str) -> Optional[str]:
    """
    Safely read a text file.
    Returns file content or None if unsafe/unreadable.
    """
    if not is_safe_file(path):
        return None

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None
