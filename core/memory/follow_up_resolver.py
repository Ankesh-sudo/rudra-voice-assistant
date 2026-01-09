"""
Follow-Up Resolver

Uses Context Pack to resolve ambiguous follow-ups.
"""

from core.memory.priority_scorer import PriorityScorer


class FollowUpResolver:
    def __init__(self):
        self.scorer = PriorityScorer()

    def resolve(self, *, tokens: list[str], context_pack: dict) -> dict | None:
        """
        Return resolved info or None if unresolved.
        """
        recent = context_pack.get("recent_conversation", [])

        if not recent:
            return None

        # Simple rule: last meaningful user action
        last = recent[-1]

        return {
            "resolved_intent": last.get("intent"),
            "resolved_entities": last.get("entities", {}),
        }
