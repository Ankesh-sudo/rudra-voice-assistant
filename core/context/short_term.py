from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ShortTermContext:
    last_intent: Optional[str] = None
    last_entities: Dict[str, Any] = field(default_factory=dict)

    def update(self, intent: str, entities: Dict[str, Any] | None = None):
        self.last_intent = intent
        if entities:
            self.last_entities.update(entities)

    def clear(self):
        self.last_intent = None
        self.last_entities.clear()
