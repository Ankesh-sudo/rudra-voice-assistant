from loguru import logger
from core.storage.mysql import verify_connection

class Assistant:
    def __init__(self):
        self.name = "Rudra"

    def run(self):
        logger.info("Assistant initialized: {}", self.name)

        ok, msg = verify_connection()
        if ok:
            logger.info("MySQL connection OK: {}", msg)
        else:
            logger.error("MySQL connection FAILED: {}", msg)

        logger.info("Day 1 complete. Core system is stable.")
