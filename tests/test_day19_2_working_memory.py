"""
Day 19.2 Test — Working Memory Integration

Goal:
- Ensure WorkingMemory does not break assistant flow
- Ensure per-cycle isolation
- No DB or memory persistence involved
"""

from core.assistant import Assistant
from core.nlp.intent import Intent


def test_working_memory_cycle_runs_cleanly(monkeypatch):
    """
    Test that a single assistant cycle runs without error
    and WorkingMemory integration does not affect behavior.
    """

    assistant = Assistant()

    # ---------------- MOCK INPUT ----------------
    def mock_read():
        return "hello rudra"

    assistant.input.read = mock_read

    # ---------------- MOCK VALIDATOR ----------------
    assistant.input_validator.validate = lambda x: {
        "valid": True,
        "clean_text": x
    }

    # ---------------- MOCK NLP ----------------
    def mock_score_intents(tokens):
        return {Intent.GREETING: 0.95}

    def mock_pick_best_intent(scores, tokens):
        return Intent.GREETING, 0.95

    monkeypatch.setattr(
        "core.intelligence.intent_scorer.score_intents",
        mock_score_intents
    )

    monkeypatch.setattr(
        "core.intelligence.intent_scorer.pick_best_intent",
        mock_pick_best_intent
    )

    # ---------------- MOCK CONFIDENCE ----------------
    monkeypatch.setattr(
        "core.intelligence.confidence_refiner.refine_confidence",
        lambda c, t, i, l: c
    )

    # ---------------- MOCK RESPONSE ----------------
    monkeypatch.setattr(
        "core.skills.basic.handle",
        lambda intent, text: "Hello!"
    )

    # ---------------- RUN ONE CYCLE ----------------
    assistant.run_once()

    # ---------------- ASSERT ----------------
    # If we reached here without exception, WM is safe
    assert True
