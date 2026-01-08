from loguru import logger

from core.input.input_validator import InputValidator
from core.storage.mysql import verify_connection
from core.input_controller import InputController
from core.nlp.normalizer import normalize_text
from core.nlp.intent import Intent
from core.skills.basic import handle as basic_handle
from core.context.short_term import ShortTermContext
from core.context.long_term import save_message
from core.intelligence.intent_scorer import score_intents, pick_best_intent
from core.intelligence.confidence_refiner import refine_confidence
from core.actions.action_executor import ActionExecutor

from core.control.global_interrupt import GLOBAL_INTERRUPT
from core.control.interrupt_words import INTERRUPT_KEYWORDS


INTENT_CONFIDENCE_THRESHOLD = 0.65

CLARIFICATION_MESSAGES = [
    "I’m not sure what you meant. Can you rephrase?",
    "Could you explain that a bit more?",
    "I didn’t fully get that. What would you like to do?",
]

IDLE, ACTIVE, WAITING = "idle", "active", "waiting"


class Assistant:
    def __init__(self):
        self.input = InputController()
        self.running = True
        self.ctx = ShortTermContext()
        self.input_validator = InputValidator()
        self.state = IDLE
        self.silence_count = 0

        self.action_executor = ActionExecutor()

        # Day 17.6 slot state
        self.pending_intent = None
        self.pending_args = {}
        self.missing_args = []

        self.clarify_index = 0

    def next_clarification(self):
        msg = CLARIFICATION_MESSAGES[self.clarify_index]
        self.clarify_index = (self.clarify_index + 1) % len(CLARIFICATION_MESSAGES)
        return msg

    def _is_global_interrupt(self, text: str) -> bool:
        if not text:
            return False
        return text.lower().strip() in INTERRUPT_KEYWORDS

    def _handle_global_interrupt(self, text: str):
        logger.warning(f"Global interrupt triggered by: {text}")

        GLOBAL_INTERRUPT.trigger()

        # Reset ONLY execution-related state
        self.pending_intent = None
        self.pending_args = {}
        self.missing_args = []

        self.input.reset_execution_state()

        GLOBAL_INTERRUPT.clear()

        print("Rudra > Okay, stopped.")

    def run(self):
        logger.info("Day 18.1 — Global Interrupts enabled")

        while self.running:
            raw_text = self.input.read()

            # 🔴 GLOBAL INTERRUPT — ABSOLUTE PRIORITY
            if self._is_global_interrupt(raw_text):
                self._handle_global_interrupt(raw_text)
                continue

            # ❌ DO NOT SLEEP DURING SLOT RECOVERY
            if not raw_text and not self.pending_intent:
                self.silence_count += 1
                if self.silence_count == 1:
                    print("Rudra > I'm listening.")
                elif self.silence_count >= 2:
                    print("Rudra > Going to sleep.")
                    self.state = IDLE
                continue

            self.silence_count = 0

            validation = self.input_validator.validate(raw_text)
            if not validation["valid"]:
                print("Rudra > Please repeat.")
                continue

            clean_text = validation["clean_text"]
            tokens = normalize_text(clean_text)

            # ======================================
            # SLOT RECOVERY MODE
            # ======================================
            if self.pending_intent:
                # Abort slot recovery if interrupt occurred mid-loop
                if GLOBAL_INTERRUPT.is_triggered():
                    self._handle_global_interrupt("interrupt")
                    continue

                new_args = self.action_executor.fill_missing(
                    self.pending_intent, clean_text, self.missing_args
                )
                self.pending_args.update(new_args)

                still_missing = [
                    k for k in self.missing_args if not self.pending_args.get(k)
                ]

                if still_missing:
                    print(f"Rudra > Please provide {', '.join(still_missing)}.")
                    self.missing_args = still_missing
                    continue

                result = self.action_executor.execute(
                    self.pending_intent,
                    clean_text,
                    confidence=0.85,
                    replay_args=self.pending_args,
                )

                print(f"Rudra > {result.get('message')}")

                self.ctx.update(
                    self.pending_intent.value,
                    text=clean_text,
                    entities=result.get("args"),
                )

                self.pending_intent = None
                self.pending_args = {}
                self.missing_args = []
                continue

            # ======================================
            # NORMAL FLOW
            # ======================================
            scores = score_intents(tokens)
            intent, confidence = pick_best_intent(scores, tokens)
            confidence = refine_confidence(
                confidence, tokens, intent.value, self.ctx.last_intent
            )

            if confidence < INTENT_CONFIDENCE_THRESHOLD or intent == Intent.UNKNOWN:
                print(f"Rudra > {self.next_clarification()}")
                continue

            missing = self.action_executor.get_missing_args(intent, clean_text)
            if missing:
                self.pending_intent = intent
                self.pending_args = {}
                self.missing_args = missing
                print(f"Rudra > Please provide {', '.join(missing)}.")
                continue

            save_message("user", clean_text, intent.value)

            if intent == Intent.EXIT:
                print("Rudra > Goodbye!")
                break

            if intent in (Intent.GREETING, Intent.HELP):
                response = basic_handle(intent, clean_text)
            else:
                result = self.action_executor.execute(intent, clean_text, confidence)
                response = result.get("message", "Done.")

            print(f"Rudra > {response}")
            save_message("assistant", response, intent.value)
            self.ctx.update(intent.value)
