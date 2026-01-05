"""
Action Executor with Confidence Gating
Day 14.4 — Argument Capture & Safe Replay
"""

import logging
from typing import Dict, Any, Optional

from core.nlp.intent import Intent
from core.nlp.argument_extractor import ArgumentExtractor
from core.skills.system_actions import SystemActions
from core.context.follow_up import FollowUpContext

logger = logging.getLogger(__name__)


class ActionExecutor:
    def __init__(self, config=None):
        self.config = config
        self.argument_extractor = ArgumentExtractor(config)
        self.system_actions = SystemActions(config)

        # Day 13.2 — SAFE follow-up memory
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
        replay_args: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        logger.info(f"Intent={intent.value} confidence={confidence:.2f}")

        # ---------- DAY 14.4: REPLAY ARGUMENTS ----------
        if replay_args:
            logger.info("[DAY 14.4] Using replay arguments: %s", replay_args)
            args = replay_args
        else:
            # ---------- DAY 13.2 FOLLOW-UP (SAFE) ----------
            followup = self._try_follow_up(text, confidence)
            if followup:
                return followup
            # ----------------------------------------------

            # ---------- CONFIDENCE CHECK ----------
            allowed, reason = self._check_confidence(intent, confidence, text)
            if not allowed:
                return {
                    "success": False,
                    "message": self._rejection_message(reason, confidence),
                    "confidence": confidence,
                    "executed": False,
                    "reason": reason
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
                    "executed": False
                }

        # ---------- EXECUTE ----------
        result = self._execute_intent(intent, args)

        # ---------- STORE CONTEXT FOR REPLAY ----------
        if result.get("success", False):
            action_name = self._intent_to_action_name(intent)

            # 🔒 Store resolved args (CRITICAL FIX)
            self.follow_up_context.add_context(
                action_name,
                {
                    "entities": args,
                    "result": result
                },
                text
            )

        self._log(intent, text, confidence, result)

        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "confidence": confidence,
            "executed": True,
            "args": args,          # 🔽 returned for ShortTermContext
            "result": result
        }

    # =====================================================
    # DAY 13.2 FOLLOW-UP (SAFE)
    # =====================================================
    def _try_follow_up(self, text: str, confidence: float) -> Optional[Dict[str, Any]]:
        text_lower = text.lower()

        follow_words = ["it", "that", "there", "again", "same"]
        if not any(w in text_lower for w in follow_words):
            return None

        context, ref_type = self.follow_up_context.resolve_reference(text)
        if not context:
            return None

        original_action = context["action"]
        entities = context["entities"]

        safe_action = self._map_safe_followup_action(original_action, text_lower)
        if not safe_action:
            return None

        args = entities.copy()

        try:
            result = self._execute_followup_action(safe_action, args)

            if result.get("success", False):
                self.follow_up_context.add_context(
                    safe_action,
                    {"entities": args, "result": result},
                    text
                )

            self._log_followup(text, confidence, result)

            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "confidence": min(1.0, confidence * 1.1),
                "executed": True,
                "args": args,
                "result": result,
                "is_followup": True
            }

        except Exception as e:
            logger.error(f"Follow-up failed safely: {e}")
            return None

    def _map_safe_followup_action(self, original_action: str, text: str) -> Optional[str]:
        allowed = {
            "open_browser",
            "open_terminal",
            "open_file_manager",
            "open_file",
            "search_web",
            "list_files",
        }

        if original_action not in allowed:
            return None

        if "search" in text and original_action == "open_browser":
            return "search_web"

        return original_action

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
                target=args.get("target")
            )

        if action == "list_files":
            return self.system_actions.list_files(
                path=args.get("path"), target=args.get("target")
            )

        return {"success": False, "message": f"Unsupported follow-up action: {action}"}

    # =====================================================
    # CORE EXECUTION (Day 12)
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
                target=args.get("target")
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
        basic_intents = {Intent.GREETING, Intent.HELP, Intent.EXIT}

        if intent in basic_intents:
            return True, "basic intent"

        if confidence < self.min_confidence:
            return False, "low confidence"

        if any(w in text.lower() for w in ["it", "that", "there"]) and confidence < 0.6:
            return False, "ambiguous command"

        if intent == Intent.OPEN_TERMINAL and confidence < self.high_confidence:
            return False, "dangerous action"

        return True, "ok"

    def _rejection_message(self, reason: str, confidence: float) -> str:
        if reason == "low confidence":
            return f"I'm not confident enough ({confidence:.0%}). Please rephrase."
        if reason == "ambiguous command":
            return "I'm not sure what you mean. Please be more specific."
        if reason == "dangerous action":
            return "I need to be more certain before doing that."
        return "I can't perform that action."

    def _intent_to_action_name(self, intent: Intent) -> str:
        return {
            Intent.OPEN_BROWSER: "open_browser",
            Intent.OPEN_TERMINAL: "open_terminal",
            Intent.OPEN_FILE_MANAGER: "open_file_manager",
            Intent.OPEN_FILE: "open_file",
            Intent.SEARCH_WEB: "search_web",
            Intent.LIST_FILES: "list_files",
        }.get(intent, "unknown")

    def _log(self, intent: Intent, text: str, confidence: float, result: Dict[str, Any]):
        self.action_history.append({
            "intent": intent.value,
            "text": text,
            "confidence": confidence,
            "success": result.get("success", False),
        })
        if len(self.action_history) > 20:
            self.action_history.pop(0)

    def _log_followup(self, text: str, confidence: float, result: Dict[str, Any]):
        self.action_history.append({
            "intent": "followup",
            "text": text,
            "confidence": confidence,
            "success": result.get("success", False),
        })
        if len(self.action_history) > 20:
            self.action_history.pop(0)
