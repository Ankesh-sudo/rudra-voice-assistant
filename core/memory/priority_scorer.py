"""
Priority Scorer

Scores relevance of context items for follow-ups.
Rule-based, deterministic.
"""

class PriorityScorer:
    def score_recent(self, item: dict) -> int:
        """
        Score STM items.
        Higher = more relevant.
        """
        score = 0

        # Most recent messages are more important
        if item.get("is_recent"):
            score += 3

        # Same intent continuity
        if item.get("same_intent"):
            score += 2

        return score

    def score_fact(self, fact: dict, intent: str | None) -> int:
        """
        Score LTM facts.
        """
        score = 0

        # Intent relevance (simple rule)
        if intent and fact.get("type") == intent:
            score += 2

        return score
