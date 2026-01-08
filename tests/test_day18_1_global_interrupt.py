import time

from core.control.global_interrupt import GLOBAL_INTERRUPT
from core.control.interrupt_words import INTERRUPT_KEYWORDS
from core.actions.action_executor import ActionExecutor
from core.input_controller import InputController
from core.nlp.intent import Intent


def test_interrupt_flag_basic():
    GLOBAL_INTERRUPT.clear()
    assert not GLOBAL_INTERRUPT.is_triggered()

    GLOBAL_INTERRUPT.trigger()
    assert GLOBAL_INTERRUPT.is_triggered()

    GLOBAL_INTERRUPT.clear()
    assert not GLOBAL_INTERRUPT.is_triggered()


def test_interrupt_keywords_match():
    for word in INTERRUPT_KEYWORDS:
        assert isinstance(word, str)
        assert word == word.lower()


def test_action_executor_interrupt_abort():
    executor = ActionExecutor()

    GLOBAL_INTERRUPT.trigger()

    result = executor.execute(
        intent=Intent.OPEN_BROWSER,
        text="open browser youtube",
        confidence=0.9,
    )

    assert result["success"] is False
    assert result["executed"] is False
    assert "cancel" in result["message"].lower()

    GLOBAL_INTERRUPT.clear()


def test_input_controller_reset_execution_state():
    ic = InputController()

    ic.active = True
    ic.last_active_time = time.time()

    ic.reset_execution_state()

    assert ic.active is False
    assert ic.last_active_time == 0


def test_interrupt_does_not_persist():
    GLOBAL_INTERRUPT.trigger()
    assert GLOBAL_INTERRUPT.is_triggered()

    GLOBAL_INTERRUPT.clear()
    assert not GLOBAL_INTERRUPT.is_triggered()
