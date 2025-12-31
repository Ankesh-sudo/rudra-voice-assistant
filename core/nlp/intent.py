from enum import Enum

class Intent(Enum):
    GREETING = "greeting"
    HELP = "help"
    EXIT = "exit"
    NOTE_CREATE = "note_create"
    NOTE_READ = "note_read"
    OPEN_BROWSER = "open_browser"
    OPEN_TERMINAL = "open_terminal" 
    OPEN_FILE_MANAGER = "open_file_manager"
    OPEN_FILE = "open_file"
    SEARCH_WEB = "search_web"
    PLAY_MEDIA = "play_media"
    CONTROL_VOLUME = "control_volume"
    LIST_FILES = "list_files"
    UNKNOWN = "unknown"


def detect_intent(tokens: list[str]) -> Intent:
    if not tokens:
        return Intent.UNKNOWN

    if any(t in ("hi", "hello", "hey") for t in tokens):
        return Intent.GREETING

    if any(t in ("help", "commands") for t in tokens):
        return Intent.HELP

    if any(t in ("exit", "quit", "bye") for t in tokens):
        return Intent.EXIT
    
    if "note" in tokens and any(t in ("save", "write", "take") for t in tokens):
        return Intent.NOTE_CREATE

    if "note" in tokens and any(t in ("read", "show", "list") for t in tokens):
        return Intent.NOTE_READ

    return Intent.UNKNOWN
