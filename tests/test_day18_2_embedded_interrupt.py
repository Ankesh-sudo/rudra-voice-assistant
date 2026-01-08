import pytest

from core.assistant import Assistant


class DummyInput:
    """
    Controlled input that stops the assistant loop after one read.
    """
    def __init__(self, inputs, assistant):
        self.inputs = inputs
        self.index = 0
        self.assistant = assistant

    def read(self):
        if self.index >= len(self.inputs):
            # stop loop after first cycle
            self.assistant.running = False
            return ""

        value = self.inputs[self.index]
        self.index += 1
        return value

    def reset_execution_state(self):
        pass


def run_single_cycle(text, capsys):
    assistant = Assistant()
    assistant.input = DummyInput([text], assistant)
    assistant.run()
    return capsys.readouterr().out


# ==========================================
# TESTS
# ==========================================

def test_embedded_interrupt_at_end(capsys):
    out = run_single_cycle("open youtube stop", capsys)
    assert "Okay, stopped." in out


def test_embedded_interrupt_in_middle(capsys):
    out = run_single_cycle("search web cancel now", capsys)
    assert "Okay, stopped." in out


def test_abort_keyword_triggers_interrupt(capsys):
    out = run_single_cycle("open file abort", capsys)
    assert "Okay, stopped." in out


def test_negated_interrupt_does_not_trigger(capsys):
    out = run_single_cycle("don't stop the music", capsys)
    assert "Okay, stopped." not in out


def test_substring_interrupt_does_not_trigger(capsys):
    out = run_single_cycle("unstoppable force", capsys)
    assert "Okay, stopped." not in out


def test_exact_match_interrupt_still_works(capsys):
    out = run_single_cycle("stop", capsys)
    assert "Okay, stopped." in out
