"""
Action Executor with Confidence Gating
Day 15 — Intent Isolation, Safe Replay, API-Compatible
"""

import logging
from typing import Dict, Any, Optional

from core.nlp.intent import Intent
from core.nlp.argument_extractor import ArgumentExtractor
from core.skills.system_actions import SystemActions
from core.context.follow_up import FollowUpContext

logger = logging.getLogger(__name__)


# -------------------------------
# Day 15 — Intent classification
# -------------------------------
DANGEROUS_INTENTS = {
    Intent.OPEN_TERMINAL,
}

INTENT_CLASS = {
    Intent.OPEN_BROWSER: "system",
    Intent.SEARCH_WEB: "system",
    Intent.OPEN_FILE_MANAGER: "filesystem",
    Intent.OPEN_FILE: "filesystem",
    Intent.LIST_FILES: "filesystem",
    Intent.OPEN_TERMINAL: "dangerous",
}


class ActionExecutor:
    def __init__(self, config=None):
        self.config = config
        self.argument_extractor = ArgumentExtractor(config)
        self.system_actions = SystemActions(config)

        # Existing follow-up memory (UNCHANGED)
        self.follow_up_context = FollowUpContext()

        self.min_confidence = 0.3
        self.high_confidence = 0.7

        self.action_history = []

    # =====================================================
    # PUBLIC ENTRY
    # =====================================================
    def execute(
        self,
        intent: Intent,
        text: str,
        confidence: float,
        replay_args: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        logger.info(f"Intent={intent.value} confidence={confidence:.2f}")

        # ---------- REPLAY PATH (Day 15) ----------
        if replay_args:
            logger.info("[DAY 15] Using replay arguments")
            args = replay_args

        else:
            # ---------- FOLLOW-UP PATH ----------
            followup = self._try_follow_up(text, confidence)
            if followup:
                return followup

            # ---------- CONFIDENCE CHECK ----------
            allowed, reason = self._check_confidence(intent, confidence, text)
            if not allowed:
                return {
                    "success": False,
                    "message": self._rejection_message(reason, confidence),
                    "confidence": confidence,
                    "executed": False,
                    "reason": reason,
                }

            # ---------- ARGUMENT EXTRACTION ----------
            args = self.argument_extractor.extract_for_intent(
                text, intent.value
            )

            valid, msg = self.argument_extractor.validate_arguments(
                args, intent.value
            )
            if not valid:
                return {
                    "success": False,
                    "message": msg,
                    "confidence": confidence,
                    "executed": False,
                }

        # ---------- EXECUTION ----------
        result = self._execute_intent(intent, args)

        # ---------- STORE CONTEXT (API-SAFE) ----------
        if result.get("success", False):
            self.follow_up_context.add_context(
                intent.value,
                {
                    "entities": args,
                    "intent_class": INTENT_CLASS.get(intent),
                    "danger": intent in DANGEROUS_INTENTS,
                },
                text,  # ← positional (FIXED)
            )

        self._log(intent, text, confidence, result)

        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "confidence": confidence,
            "executed": True,
            "args": args,
            "result": result,
        }

    # =====================================================
    # FOLLOW-UP HANDLING (SAFE)
    # =====================================================
    def _try_follow_up(self, text: str, confidence: float) -> Optional[Dict[str, Any]]:
        text_lower = text.lower()

        if not any(w in text_lower for w in ["it", "that", "there", "again", "same"]):
            return None

        context, _ = self.follow_up_context.resolve_reference(text)
        if not context:
            return None

        if context.get("danger"):
            logger.warning("[DAY 15 BLOCK] Dangerous intent replay blocked")
            return {
                "success": False,
                "message": "I won’t repeat that action for safety.",
                "confidence": confidence,
                "executed": False,
            }

        intent_name = context["action"]
        args = context["entities"]

        result = self._execute_followup_action(intent_name, args)

        if result.get("success", False):
            self.follow_up_context.add_context(
                intent_name,
                context,
                text,  # ← positional (FIXED)
            )

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
    # FOLLOW-UP EXECUTION
    # =====================================================
    def _execute_followup_action(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if action == "open_browser":
            return self.system_actions.open_browser(
                url=args.get("url"), target=args.get("target")
            )

        if action == "search_web":
            return self.system_actions.search_web(
                query=args.get("query"), target=args.get("target")
            )

        if action == "open_file_manager":
            return self.system_actions.open_file_manager(
                path=args.get("path"), target=args.get("target")
            )

        if action == "open_terminal":
            return self.system_actions.open_terminal(
                command=args.get("command"), target=args.get("target")
            )

        if action == "open_file":
            return self.system_actions.open_file(
                filename=args.get("filename"),
                full_path=args.get("full_path"),
                target=args.get("target"),
            )

        if action == "list_files":
            return self.system_actions.list_files(
                path=args.get("path"), target=args.get("target")
            )

        return {"success": False, "message": f"Unsupported follow-up action: {action}"}

    # =====================================================
    # CORE EXECUTION
    # =====================================================
    def _execute_intent(self, intent: Intent, args: Dict[str, Any]) -> Dict[str, Any]:
        if intent == Intent.OPEN_BROWSER:
            return self.system_actions.open_browser(
                url=args.get("url"), target=args.get("target")
            )

        if intent == Intent.OPEN_TERMINAL:
            return self.system_actions.open_terminal(
                command=args.get("command"), target=args.get("target")
            )

        if intent == Intent.OPEN_FILE_MANAGER:
            return self.system_actions.open_file_manager(
                path=args.get("path"), target=args.get("target")
            )

        if intent == Intent.SEARCH_WEB:
            return self.system_actions.search_web(
                query=args.get("query"), target=args.get("target")
            )

        if intent == Intent.OPEN_FILE:
            return self.system_actions.open_file(
                filename=args.get("filename"),
                full_path=args.get("full_path"),
                target=args.get("target"),
            )

        if intent == Intent.LIST_FILES:
            return self.system_actions.list_files(
                path=args.get("path"), target=args.get("target")
            )

        return {"success": False, "message": f"Intent not implemented: {intent.value}"}

    # =====================================================
    # SAFETY + UTILS
    # =====================================================
    def _check_confidence(self, intent: Intent, confidence: float, text: str):
        if confidence < self.min_confidence:
            return False, "low confidence"

        if intent in DANGEROUS_INTENTS and confidence < self.high_confidence:
            return False, "dangerous action"

        return True, "ok"

    def _rejection_message(self, reason: str, confidence: float) -> str:
        if reason == "low confidence":
            return f"I'm not confident enough ({confidence:.0%}). Please rephrase."
        if reason == "dangerous action":
            return "I need to be more certain before doing that."
        return "I can’t perform that action."

    def _log(self, intent: Intent, text: str, confidence: float, result: Dict[str, Any]):
        self.action_history.append(
            {
                "intent": intent.value,
                "text": text,
                "confidence": confidence,
                "success": result.get("success", False),
            }
        )
        if len(self.action_history) > 20:
            self.action_history.pop(0)
