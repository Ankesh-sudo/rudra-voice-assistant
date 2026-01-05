from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ShortTermContext:
    # Last successfully executed intent (string value)
    last_intent: Optional[str] = None

    # Original clean text used for execution (e.g. "open browser github")
    last_text: Optional[str] = None

    # Optional extracted entities / arguments
    last_entities: Dict[str, Any] = field(default_factory=dict)

    def update(
        self,
        intent: str,
        text: Optional[str] = None,
        entities: Dict[str, Any] | None = None
    ):
        """
        Update context after a successful execution.
        - intent: intent.value (string)
        - text: clean_text used for execution
        - entities: optional extracted arguments
        """
        self.last_intent = intent

        if text is not None:
            self.last_text = text

        if entities:
            self.last_entities.update(entities)

    def has_last_action(self) -> bool:
        """
        Returns True only if we have enough information
        to safely replay an action.
        """
        return self.last_intent is not None and self.last_text is not None

    def clear(self):
        self.last_intent = None
        self.last_text = None
        self.last_entities.clear()
