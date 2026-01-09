from loguru import logger

from core.input.input_validator import InputValidator
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
from core.control.interrupt_policy import INTERRUPT_POLICY  # Day 18.4

# Day 19.2
from core.memory.working_memory import WorkingMemory

# Day 20.1
from core.memory.context_pack import ContextPackBuilder

# 🆕 Day 20.2
from core.memory.follow_up_resolver import FollowUpResolver


INTENT_CONFIDENCE_THRESHOLD = 0.65

CLARIFICATION_MESSAGES = [
    "I’m not sure what you meant. Can you rephrase?",
    "Could you explain that a bit more?",
    "I didn’t fully get that. What would you like to do?",
]

IDLE, ACTIVE, WAITING = "idle", "active", "waiting"

NEGATION_TOKENS = {"dont", "do", "not", "never", "no"}


class Assistant:
    def __init__(self):
        self.input = InputController()
        self.running = True
        self.ctx = ShortTermContext()
        self.input_validator = InputValidator()
        self.state = IDLE

        self.action_executor = ActionExecutor()

        # Slot recovery (Day 17.6)
        self.pending_intent = None
        self.pending_args = {}
        self.missing_args = []

        self.clarify_index = 0

    # =================================================
    # UTIL
    # =================================================
    def next_clarification(self):
        msg = CLARIFICATION_MESSAGES[self.clarify_index]
        self.clarify_index = (self.clarify_index + 1) % len(CLARIFICATION_MESSAGES)
        return msg

    def _get_interrupt_policy(self, intent: Intent | None) -> str:
        if not intent:
            return "HARD"
        return INTERRUPT_POLICY.get(intent, "HARD")

    # =================================================
    # DAY 18.2+ — EMBEDDED INTERRUPT DETECTION
    # =================================================
    def _detect_embedded_interrupt(self, tokens: list[str]) -> bool:
        for idx, token in enumerate(tokens):
            if token in INTERRUPT_KEYWORDS:
                if idx > 0 and tokens[idx - 1] in NEGATION_TOKENS:
                    return False
                return True
        return False

    # =================================================
    # DAY 18.4 — INTENT-AWARE INTERRUPT HANDLER
    # =================================================
    def _handle_interrupt(self, source: str, intent: Intent | None):
        policy = self._get_interrupt_policy(intent)

        logger.warning(f"Interrupt triggered ({source}) | policy={policy}")

        if policy == "IGNORE":
            return

        if policy == "SOFT":
            print("Rudra > Do you want me to stop this action?")
            return

        GLOBAL_INTERRUPT.trigger()
        self.action_executor.cancel_pending()

        self.pending_intent = None
        self.pending_args = {}
        self.missing_args = []

        self.input.reset_execution_state()
        print("Rudra > Okay, stopped.")
        GLOBAL_INTERRUPT.clear()

    # =================================================
    # CORE SINGLE CYCLE (Day 20.2)
    # =================================================
    def _cycle(self):
        # Working Memory
        wm = WorkingMemory()

        # Context Pack (read-only)
        context_builder = ContextPackBuilder()
        context_pack = context_builder.build()

        # Follow-up resolver (rule-based)
        follow_up_resolver = FollowUpResolver()

        raw_text = self.input.read()
        if not raw_text and not self.pending_intent:
            return

        validation = self.input_validator.validate(raw_text)
        if not validation["valid"]:
            print("Rudra > Please repeat.")
            return

        clean_text = validation["clean_text"]
        tokens = normalize_text(clean_text)

        # 🔴 INTERRUPT
        current_intent = self.pending_intent
        if self._detect_embedded_interrupt(tokens):
            self._handle_interrupt("embedded", current_intent)
            wm.mark_interrupted()
            return

        # ================= SLOT RECOVERY =================
        if self.pending_intent:
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
                return

            self.action_executor.execute(
                self.pending_intent,
                clean_text,
                confidence=0.85,
                replay_args=self.pending_args,
            )

            self.pending_intent = None
            self.pending_args = {}
            self.missing_args = []
            return

        # ================= NORMAL FLOW =================
        scores = score_intents(tokens)
        intent, confidence = pick_best_intent(scores, tokens)
        confidence = refine_confidence(
            confidence, tokens, intent.value, self.ctx.last_intent
        )

        wm.set_intent(intent.value, confidence)

        # 🆕 Memory-aware ambiguity handling
        if confidence < INTENT_CONFIDENCE_THRESHOLD or intent == Intent.UNKNOWN:
            resolved = follow_up_resolver.resolve(
                tokens=tokens,
                context_pack=context_pack
            )

            if resolved:
                try:
                    intent = Intent(resolved["resolved_intent"])
                    confidence = 0.7
                except Exception:
                    print(f"Rudra > {self.next_clarification()}")
                    return
            else:
                print(f"Rudra > {self.next_clarification()}")
                return

        missing = self.action_executor.get_missing_args(intent, clean_text)
        if missing:
            self.pending_intent = intent
            self.missing_args = missing
            print(f"Rudra > Please provide {', '.join(missing)}.")
            return

        save_message("user", clean_text, intent.value)

        if intent == Intent.EXIT:
            print("Rudra > Goodbye!")
            self.running = False
            return

        if intent in (Intent.GREETING, Intent.HELP):
            response = basic_handle(intent, clean_text)
        else:
            result = self.action_executor.execute(intent, clean_text, confidence)
            response = result.get("message", "Done.")

        print(f"Rudra > {response}")
        save_message("assistant", response, intent.value)
        self.ctx.update(intent.value)

    # =================================================
    # PRODUCTION LOOP
    # =================================================
    def run(self):
        logger.info("Day 20.2 — Memory-aware follow-ups enabled")
        while self.running:
            self._cycle()

    # =================================================
    # TEST-SAFE SINGLE CYCLE
    # =================================================
    def run_once(self):
        self._cycle()
