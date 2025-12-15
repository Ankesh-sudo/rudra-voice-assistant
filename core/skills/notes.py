from sqlalchemy import select
from core.storage.mysql import get_session
from core.storage.notes_models import Note

def save_note(text: str) -> str:
    lowered = text.lower()

    for phrase in ["save note", "write note", "take note"]:
        if phrase in lowered:
            content = lowered.split(phrase, 1)[1].strip()
            break
    else:
        return "I did not catch what to save."

    # very short or garbage content → ask again
    if len(content.split()) < 3:
        return "Please say the note content again."

    with get_session() as session:
        session.add(Note(content=content))

    return f"I saved this note: {content}"



def read_notes(limit: int = 5) -> str:
    with get_session() as session:
        stmt = select(Note.content).order_by(Note.created_at.desc()).limit(limit)
        notes = session.execute(stmt).scalars().all()

    if not notes:
        return "You have no notes."

    response = "Your recent notes:\n"
    for i, content in enumerate(notes, 1):
        response += f"{i}. {content}\n"

    return response.strip()
