import os
from typing import Optional
from core.system.config import HOME_DIR


# Allowed base directories (sandbox)
ALLOWED_DIRS = {
    "home": HOME_DIR,
    "desktop": os.path.join(HOME_DIR, "Desktop"),
    "downloads": os.path.join(HOME_DIR, "Downloads"),
    "documents": os.path.join(HOME_DIR, "Documents"),
}


def resolve_base_path(text: str) -> Optional[str]:
    """
    Resolve spoken directory names to absolute paths.
    Only allows HOME and known subfolders.
    """
    text = text.lower()

    for key, path in ALLOWED_DIRS.items():
        if key in text:
            if os.path.isdir(path):
                return path
            return None

    # Default to HOME if nothing specified
    return HOME_DIR


def resolve_file_path(filename: str, base_dir: str) -> Optional[str]:
    """
    Resolve a file path safely inside base_dir.
    Prevents path traversal.
    """
    if not filename:
        return None

    # Normalize
    filename = filename.strip().replace("..", "")
    candidate = os.path.abspath(os.path.join(base_dir, filename))

    # Sandbox enforcement
    if not candidate.startswith(HOME_DIR):
        return None

    if os.path.isfile(candidate):
        return candidate

    return None
