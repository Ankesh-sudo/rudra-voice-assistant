from core.input.voice_input import VoiceInput

_voice = VoiceInput()

def read_text() -> str:
    try:
        return _voice.listen_once()
    except KeyboardInterrupt:
        raise
    except Exception:
        # fallback to text
        return input("You > ").strip()
