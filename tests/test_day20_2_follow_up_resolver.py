from core.memory.follow_up_resolver import FollowUpResolver


def test_follow_up_resolver_returns_none_when_no_context():
    resolver = FollowUpResolver()
    result = resolver.resolve(tokens=["do", "that"], context_pack={})
    assert result is None
