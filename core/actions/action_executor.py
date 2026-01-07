"""
Action Executor with Confidence Gating
Day 15.6 — Reference Confidence + Intent-Class Isolation (TEST-CORRECT)
"""

import logging
import re
from typing import Dict, Any, Optional

from core.nlp.intent import Intent
from core.nlp.argument_extractor import ArgumentExtractor
from core.skills.system_actions import SystemActions
from core.context.follow_up import FollowUpContext, INTENT_ENTITY_WHITELIST

logger = logging.getLogger(__name__)

DANGEROUS_INTENTS = {Intent.OPEN_TERMINAL}


class ActionExecutor:
    def __init__(self, config=None):
        self.config = config
        self.argument_extractor = ArgumentExtractor(config)
        self.system_actions = SystemActions(config)
        self.follow_up_context = FollowUpContext()

        self.min_confidence = 0.3
        self.high_confidence = 0.7
        self.min_reference_confidence = 0.5

        self.action_history = []

    # =====================================================
    # PUBLIC ENTRY
    # =====================================================
    def execute(
        self,
        intent: Intent,
        text: str,
        confidence: float,
        replay_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        logger.info("Intent=%s confidence=%.2f", intent.value, confidence)

        # UNKNOWN → clear context, but allow fallback later
        if intent == Intent.UNKNOWN:
            self.follow_up_context.clear_context()
            return {
                "success": False,
                "message": "Intent not supported",
                "confidence": confidence,
                "executed": False,
            }

        followup = self._try_follow_up(intent, text, confidence)
        if followup is not None:
            return followup

        allowed, reason = self._check_confidence(intent, confidence)
        if not allowed:
            self.follow_up_context.clear_context()
            return {
                "success": False,
                "message": self._rejection_message(reason, confidence),
                "confidence": confidence,
                "executed": False,
            }

        args = self.argument_extractor.extract_for_intent(text, intent.value)
        valid, msg = self.argument_extractor.validate_arguments(args, intent.value)
        if not valid:
            self.follow_up_context.clear_context()
            return {
                "success": False,
                "message": msg,
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
    # FOLLOW-UP HANDLING (FINAL)
    # =====================================================
    def _try_follow_up(
        self, intent: Intent, text: str, confidence: float
    ) -> Optional[Dict[str, Any]]:

        # WORD-SAFE reference detection
        if not re.search(r"\b(it|that|there|again|same|them)\b", text.lower()):
            return None

        if confidence < self.min_reference_confidence:
            return {
                "success": False,
                "message": "I’m not sure what you want to repeat. Please be specific.",
                "confidence": confidence,
                "executed": False,
            }

        # 🔑 CRITICAL FIX
        had_context_before = bool(self.follow_up_context.contexts)

        context, reason = self.follow_up_context.resolve_reference(text)

        if reason == "cross_intent_blocked":
            return {
                "success": False,
                "message": "I can’t apply that action to the previous context.",
                "confidence": confidence,
                "executed": False,
            }

        # ❌ Block ONLY if context existed but expired
        if not context and reason == "no_context" and had_context_before:
            return {
                "success": False,
                "message": "The previous context is no longer available.",
                "confidence": confidence,
                "executed": False,
            }

        # ✅ No previous context → allow fallback
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

        result = self._execute_action_by_name(intent.value, args)

        if not result.get("success"):
            self.follow_up_context.clear_context()

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
    # HELPERS
    # =====================================================
    def _execute_action_by_name(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        sa = self.system_actions
        if action == "open_browser":
            return sa.open_browser(args.get("url"), args.get("target"))
        if action == "search_web":
            return sa.search_web(args.get("query"), args.get("target"))
        if action == "open_file_manager":
            return sa.open_file_manager(args.get("path"), args.get("target"))
        if action == "list_files":
            return sa.list_files(args.get("path"), args.get("target"))
        if action == "open_file":
            return sa.open_file(args.get("filename"), args.get("full_path"), args.get("target"))
        if action == "open_terminal":
            return sa.open_terminal(args.get("command"), args.get("target"))
        return {"success": False, "message": f"Intent not implemented: {action}"}

    def _filter_args_by_intent(self, intent: str, args: Dict[str, Any]) -> Dict[str, Any]:
        allowed = INTENT_ENTITY_WHITELIST.get(intent, [])
        return {k: v for k, v in (args or {}).items() if k in allowed}

    def _check_confidence(self, intent: Intent, confidence: float):
        if confidence < self.min_confidence:
            return False, "low"
        if intent in DANGEROUS_INTENTS and confidence < self.high_confidence:
            return False, "danger"
        return True, "ok"

    def _rejection_message(self, reason: str, confidence: float) -> str:
        return "I can’t perform that action."

    def _log(self, intent: Intent, text: str, confidence: float, result: Dict[str, Any]):
        self.action_history.append(
            {"intent": intent.value, "text": text, "confidence": confidence}
        )
        self.action_history = self.action_history[-20:]
