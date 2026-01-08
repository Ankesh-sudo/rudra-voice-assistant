"""
Action Executor
Day 17.6 — Confidence Gating + Follow-up + Slot Recovery (FINAL)
Day 18.1 — Global Interrupt Guard (ADDED)
"""

import logging
import re
from typing import Dict, Any, Optional, List

from core.nlp.intent import Intent
from core.nlp.argument_extractor import ArgumentExtractor
from core.skills.system_actions import SystemActions
from core.context.follow_up import FollowUpContext, INTENT_ENTITY_WHITELIST

from core.control.global_interrupt import GLOBAL_INTERRUPT  # 🔴 Day 18.1

logger = logging.getLogger(__name__)

DANGEROUS_INTENTS = {Intent.OPEN_TERMINAL}

REQUIRED_ARGS = {
    "open_browser": ["url"],
    "search_web": ["query"],
    "open_file_manager": ["path"],
    "list_files": ["path"],
    "open_file": ["filename"],
    "open_terminal": ["command"],
}


class ActionExecutor:
    def __init__(self, config=None):
        self.config = config
        self.argument_extractor = ArgumentExtractor(config)
        self.system_actions = SystemActions(config)
        self.follow_up_context = FollowUpContext()

        self.min_confidence = 0.3
        self.high_confidence = 0.7
        self.min_reference_confidence = 0.5

        self.action_history: List[Dict[str, Any]] = []

    # =====================================================
    # SLOT INSPECTION
    # =====================================================
    def get_missing_args(self, intent: Intent, text: str) -> List[str]:
        if GLOBAL_INTERRUPT.is_triggered():
            return []

        required = REQUIRED_ARGS.get(intent.value, [])
        if not required:
            return []

        args = self.argument_extractor.extract_for_intent(text, intent.value)
        return [k for k in required if not args.get(k)]

    # =====================================================
    # SLOT RECOVERY
    # =====================================================
    def fill_missing(
        self,
        intent: Intent,
        followup_text: str,
        missing: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        if GLOBAL_INTERRUPT.is_triggered():
            return {}

        args = self.argument_extractor.extract_for_intent(
            followup_text, intent.value
        ) or {}

        # Single-slot recovery → full text maps to slot
        if missing and len(missing) == 1 and not args.get(missing[0]):
            args[missing[0]] = followup_text.strip()

        return args

    # =====================================================
    # EXECUTION ENTRY
    # =====================================================
    def execute(
        self,
        intent: Intent,
        text: str,
        confidence: float,
        replay_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        # 🔴 HARD STOP — GLOBAL INTERRUPT
        if GLOBAL_INTERRUPT.is_triggered():
            logger.warning("Execution aborted due to global interrupt")
            GLOBAL_INTERRUPT.clear()
            self.follow_up_context.clear_context()
            return {
                "success": False,
                "message": "Action cancelled.",
                "confidence": confidence,
                "executed": False,
            }

        logger.info("Intent=%s confidence=%.2f", intent.value, confidence)

        # ---------------- UNKNOWN ----------------
        if intent == Intent.UNKNOWN:
            self.follow_up_context.clear_context()
            return {
                "success": False,
                "message": "Intent not supported",
                "confidence": confidence,
                "executed": False,
            }

        # ---------------- PRONOUN GUARD (GLOBAL) ----------------
        if re.search(r"\b(it|that|there|again|same|them)\b", text.lower()):
            last = (
                self.follow_up_context.contexts[-1]
                if self.follow_up_context.contexts
                else None
            )

            if not last:
                return {
                    "success": False,
                    "message": "No previous context to refer to.",
                    "confidence": confidence,
                    "executed": False,
                }

            if last.get("action") != intent.value:
                return {
                    "success": False,
                    "message": "Previous context does not apply to this action.",
                    "confidence": confidence,
                    "executed": False,
                }

        # ---------------- FOLLOW-UP ----------------
        followup = self._try_follow_up(intent, text, confidence)
        if followup is not None:
            return followup

        # ---------------- CONFIDENCE GATE ----------------
        if confidence < self.min_confidence:
            return {
                "success": False,
                "message": "I can’t perform that action.",
                "confidence": confidence,
                "executed": False,
            }

        # ---------------- ARGUMENT EXTRACTION ----------------
        args = self.argument_extractor.extract_for_intent(text, intent.value)
        if replay_args:
            args = {**args, **replay_args}

        # ---------------- SLOT CHECK ----------------
        for slot in REQUIRED_ARGS.get(intent.value, []):
            if GLOBAL_INTERRUPT.is_triggered():
                logger.warning("Interrupted during slot checking")
                GLOBAL_INTERRUPT.clear()
                return {
                    "success": False,
                    "message": "Action cancelled.",
                    "confidence": confidence,
                    "executed": False,
                }

            if not args.get(slot):
                self.follow_up_context.clear_context()
                return {
                    "success": False,
                    "message": f"Please provide {slot}.",
                    "confidence": confidence,
                    "executed": False,
                }

        # ---------------- EXECUTE ACTION ----------------
        if GLOBAL_INTERRUPT.is_triggered():
            logger.warning("Interrupted before action execution")
            GLOBAL_INTERRUPT.clear()
            return {
                "success": False,
                "message": "Action cancelled.",
                "confidence": confidence,
                "executed": False,
            }

        result = self._execute_action_by_name(intent.value, args)

        if result.get("success"):
            self.follow_up_context.add_context(
                action=intent.value,
                result={"success": True, "entities": args},
                user_input=text,
            )
        else:
            self.follow_up_context.clear_context()

        self._log(intent, text, confidence)

        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "confidence": confidence,
            "executed": True,
            "args": args,
            "result": result,
        }

    # =====================================================
    # FOLLOW-UP HANDLER (INTENT-ISOLATED)
    # =====================================================
    def _try_follow_up(
        self, intent: Intent, text: str, confidence: float
    ) -> Optional[Dict[str, Any]]:

        if GLOBAL_INTERRUPT.is_triggered():
            return {
                "success": False,
                "message": "Action cancelled.",
                "confidence": confidence,
                "executed": False,
            }

        if not re.search(r"\b(it|that|there|again|same|them)\b", text.lower()):
            return None

        if confidence < self.min_reference_confidence:
            return {
                "success": False,
                "message": "Please be more specific.",
                "confidence": confidence,
                "executed": False,
            }

        context, _ = self.follow_up_context.resolve_reference(text)
        if not context:
            return None

        if intent in DANGEROUS_INTENTS:
            self.follow_up_context.clear_context()
            return {
                "success": False,
                "message": "I won’t repeat that action for safety.",
                "confidence": confidence,
                "executed": False,
            }

        args = self._filter_args_by_intent(
            intent.value, context.get("entities", {})
        )

        if GLOBAL_INTERRUPT.is_triggered():
            return {
                "success": False,
                "message": "Action cancelled.",
                "confidence": confidence,
                "executed": False,
            }

        result = self._execute_action_by_name(intent.value, args)

        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "confidence": min(1.0, confidence * 1.1),
            "executed": True,
            "args": args,
            "result": result,
            "is_followup": True,
        }

    # =====================================================
    # ACTION DISPATCH
    # =====================================================
    def _execute_action_by_name(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        sa = self.system_actions

        if GLOBAL_INTERRUPT.is_triggered():
            return {"success": False, "message": "Action cancelled."}

        if action == "open_browser":
            return sa.open_browser(args.get("url"), args.get("target"))
        if action == "search_web":
            return sa.search_web(args.get("query"), args.get("target"))
        if action == "open_file_manager":
            return sa.open_file_manager(args.get("path"), args.get("target"))
        if action == "list_files":
            return sa.list_files(args.get("path"), args.get("target"))
        if action == "open_file":
            return sa.open_file(
                args.get("filename"), args.get("full_path"), args.get("target")
            )
        if action == "open_terminal":
            return sa.open_terminal(args.get("command"), args.get("target"))

        return {"success": False, "message": f"Intent not implemented: {action}"}

    def _filter_args_by_intent(self, intent: str, args: Dict[str, Any]) -> Dict[str, Any]:
        allowed = INTENT_ENTITY_WHITELIST.get(intent, [])
        return {k: v for k, v in (args or {}).items() if k in allowed}

    def _log(self, intent: Intent, text: str, confidence: float):
        self.action_history.append(
            {"intent": intent.value, "text": text, "confidence": confidence}
        )
        self.action_history = self.action_history[-20:]
