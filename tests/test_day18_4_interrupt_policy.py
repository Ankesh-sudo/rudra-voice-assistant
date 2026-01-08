import pytest

from core.assistant import Assistant
from core.control.global_interrupt import GLOBAL_INTERRUPT


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def run_single_cycle(assistant: Assistant, text: str):
    """
    Inject a single utterance into the assistant
    and execute exactly ONE cycle.
    """
    assistant.input.read = lambda: text
    assistant.input_validator.validate = lambda x: {
        "valid": True,
        "clean_text": x,
    }

    assistant.run_once()


@pytest.fixture
def assistant():
    GLOBAL_INTERRUPT.clear()
    return Assistant()


# -------------------------------------------------
# Tests — Day 18.4 Interrupt Policy
# -------------------------------------------------

def test_interrupt_triggers_and_clears(assistant, capsys):
    run_single_cycle(assistant, "stop")
    out = capsys.readouterr().out.lower()

    assert "okay, stopped" in out
    assert not GLOBAL_INTERRUPT.is_triggered()


def test_embedded_interrupt_cancels_execution(assistant, capsys):
    run_single_cycle(assistant, "open youtube stop")
    out = capsys.readouterr().out.lower()

    assert "okay, stopped" in out
    assert assistant.pending_intent is None
    assert not assistant.pending_args


def test_embedded_interrupt_mid_sentence(assistant, capsys):
    run_single_cycle(assistant, "search web cancel now")
    out = capsys.readouterr().out.lower()

    assert "okay, stopped" in out
    assert assistant.pending_intent is None


def test_abort_keyword_triggers_interrupt(assistant, capsys):
    run_single_cycle(assistant, "open file abort")
    out = capsys.readouterr().out.lower()

    assert "okay, stopped" in out
    assert not assistant.pending_args


def test_negated_interrupt_does_not_trigger(assistant, capsys):
    run_single_cycle(assistant, "do not stop open youtube")
    out = capsys.readouterr().out.lower()

    assert "okay, stopped" not in out


def test_interrupt_clears_slot_recovery_state(assistant, capsys):
    # Simulate slot recovery state
    assistant.pending_intent = "search_web"
    assistant.missing_args = ["query"]

    run_single_cycle(assistant, "cancel")
    out = capsys.readouterr().out.lower()

    assert "okay, stopped" in out
    assert assistant.pending_intent is None
    assert assistant.missing_args == []


def test_interrupt_policy_allows_recovery_after_clear(capsys):
    """
    After interrupt is cleared, assistant
    must continue working normally.
    """
    assistant = Assistant()

    # First cycle — interrupt
    run_single_cycle(assistant, "stop")
    _ = capsys.readouterr()  # 🔴 CLEAR BUFFER

    assert not GLOBAL_INTERRUPT.is_triggered()

    # Second cycle — normal command
    run_single_cycle(assistant, "search web python")
    out = capsys.readouterr().out.lower()

    assert "stopped" not in out
    assert "search" in out or "web" in out
