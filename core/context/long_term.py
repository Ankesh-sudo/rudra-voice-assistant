from typing import List
from sqlalchemy import select
from core.storage.mysql import get_session, get_engine
from core.storage.models import Base, Conversation

# Ensure tables exist (run once on import)
engine = get_engine()
Base.metadata.create_all(bind=engine)

def save_message(role: str, text: str, intent: str):
    with get_session() as session:
        session.add(
            Conversation(role=role, text=text, intent=intent)
        )

def recent_messages(limit: int = 5) -> List[Conversation]:
    with get_session() as session:
        stmt = (
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        return list(session.scalars(stmt))
