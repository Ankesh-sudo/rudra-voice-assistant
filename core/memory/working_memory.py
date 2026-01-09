"""
Working Memory (WM)

Scope:
- Lives only during a single user interaction
- Holds transient execution context
- Never persisted to DB
- Always reset after execution or interruption
"""

from typing import Dict, Any, List


class WorkingMemory:
    def __init__(self):
        # Intent-related
        self.current_intent: str | None = None
        self.confidence: float = 0.0

        # NLP extracted data
        self.slots: Dict[str, Any] = {}
        self.entities: Dict[str, Any] = {}

        # Control state
        self.interrupted: bool = False

        # Execution trace (for safe rollback / debugging)
        self.execution_stack: List[str] = []

    # -------- Intent Handling --------

    def set_intent(self, intent: str, confidence: float):
        self.current_intent = intent
        self.confidence = confidence

    # -------- Slot & Entity Handling --------

    def add_slot(self, key: str, value: Any):
        self.slots[key] = value

    def add_entity(self, key: str, value: Any):
        self.entities[key] = value

    # -------- Execution Control --------

    def mark_interrupted(self):
        self.interrupted = True

    def push_execution_step(self, step: str):
        self.execution_stack.append(step)

    # -------- Reset --------

    def reset(self):
        """
        Reset working memory completely.
        Must be called after:
        - Successful execution
        - Aborted execution
        - Interrupt handling
        """
        self.__init__()
