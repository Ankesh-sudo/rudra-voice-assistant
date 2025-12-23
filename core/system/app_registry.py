from loguru import logger
from core.system.executor import SystemExecutor


class AppRegistry:
    def __init__(self):
        self.executor = SystemExecutor()
        self._actions = {
            "open_browser": self.executor.open_browser,
            "open_terminal": self.executor.open_terminal,
            "open_file_manager": self.executor.open_file_manager,
        }

    def execute(self, action: str) -> bool:
        if action not in self._actions:
            return False
        return bool(self._actions[action]())
