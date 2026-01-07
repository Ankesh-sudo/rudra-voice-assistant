"""
Day 16 — Intent Confidence Gating Tests

Goal:
- Assistant must NOT execute low-confidence intents
- Assistant must ask for clarification instead
- No memory or context pollution
"""

from core.assistant import Assistant
from core.context.short_term import ShortTermContext
from core.nlp.intent import Intent


class DummyInput:
    """Fake input controller for testing."""
    def __init__(self, inputs):
        self.inputs = inputs
        self.index = 0

    def read(self):
        if self.index >= len(self.inputs):
            return None
        val = self.inputs[self.index]
        self.index += 1
        return val


class DummyExecutor:
    """Executor spy to ensure it is NOT called."""
    def __init__(self):
        self.called = False

    def execute(self, *args, **kwargs):
        self.called = True
        return {
            "success": False,
            "executed": False,
            "message": "Should not execute"
        }


def test_low_confidence_input_is_blocked(monkeypatch, capsys):
    """
    Low-confidence vague input must:
    - Not execute
    - Ask for clarification
    """

    assistant = Assistant()

    # Inject dummy input (ambiguous command)
    assistant.input = DummyInput([
        "open",   # vague → low confidence
        None
    ])

    # Inject spy executor
    spy_executor = DummyExecutor()
    assistant.action_executor = spy_executor

    # Run one loop iteration
    assistant.running = True
    assistant.run()

    captured = capsys.readouterr().out.lower()

    assert "not confident" in captured or "rephrase" in captured
    assert spy_executor.called is False


def test_noise_input_does_not_create_context(monkeypatch):
    """
    Noise input must not update short-term context.
    """

    assistant = Assistant()
    assistant.input = DummyInput([
        "uhh",
        None
    ])

    assistant.action_executor = DummyExecutor()
    assistant.run()

    assert assistant.ctx.last_intent is None


def test_valid_intent_passes_confidence_gate(monkeypatch):
    """
    Valid high-confidence intent should pass gate.
    """

    assistant = Assistant()
    assistant.input = DummyInput([
        "open browser google",
        None
    ])

    spy_executor = DummyExecutor()
    assistant.action_executor = spy_executor

    assistant.run()

    # Valid intent should reach executor
    assert spy_executor.called is True


def test_low_confidence_does_not_set_followup(monkeypatch):
    """
    Low-confidence input must not set follow-up expectation.
    """

    assistant = Assistant()
    assistant.input = DummyInput([
        "do it",
        None
    ])

    assistant.action_executor = DummyExecutor()
    assistant.run()

    assert assistant.expecting_followup is False
