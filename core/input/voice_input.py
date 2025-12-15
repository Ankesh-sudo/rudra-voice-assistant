import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from loguru import logger

MODEL_PATH = "models/vosk-model-en-us-0.22"
SAMPLE_RATE = 16000
DEVICE_INDEX = 9  # PulseAudio input (IMPORTANT)

class VoiceInput:
    def __init__(self):
        logger.info("Loading Vosk model...")
        self.model = Model(MODEL_PATH)
        self.rec = KaldiRecognizer(self.model, SAMPLE_RATE)
        self.q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning(status)
        self.q.put(bytes(indata))

    def listen_once(self) -> str:
        logger.info("Listening (speak now)...")

        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=8000,
            device=DEVICE_INDEX,   # 🔥 FIX
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):
            while True:
                data = self.q.get()
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        logger.info("Heard: {}", text)
                        return text
