from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from core.assistant import Assistant

def main():
    logger.info("Starting Rudra Assistant (Day 1 – Fresh Start)")
    assistant = Assistant()
    assistant.run()

if __name__ == "__main__":
    main()
