from threading import Event


class InterruptController:
    """
    Central interrupt state controller.
    Used to immediately stop any ongoing execution or speech.
    """

    def __init__(self):
        self._interrupt_event = Event()

    def trigger(self) -> None:
        """Activate global interrupt."""
        self._interrupt_event.set()

    def clear(self) -> None:
        """Clear interrupt state after safe reset."""
        self._interrupt_event.clear()

    def is_triggered(self) -> bool:
        """Check if interrupt is currently active."""
        return self._interrupt_event.is_set()
