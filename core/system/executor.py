import os
import shutil
import subprocess
from loguru import logger


class SystemExecutor:
    """
    Executes system-level commands.
    Day 10: Linux-safe, minimal, reversible.
    """

    def open_browser(self) -> bool:
        try:
            subprocess.Popen(
                ["xdg-open", "https://www.google.com"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info("Browser opened")
            return True
        except Exception as e:
            logger.error("Failed to open browser: {}", e)
            return False


    @staticmethod
    def open_terminal() -> bool:
        try:
            subprocess.Popen(
                ["xterm"],
                env=os.environ,
                start_new_session=True
            )
            logger.info("Terminal opened via xterm")
            return True
        except Exception as e:
            logger.error("Failed to open terminal: {}", e)
            return False


    def open_file_manager(self) -> bool:
        try:
            subprocess.Popen(
                ["xdg-open", "."],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info("File manager opened")
            return True
        except Exception as e:
            logger.error("Failed to open file manager: {}", e)
            return False
