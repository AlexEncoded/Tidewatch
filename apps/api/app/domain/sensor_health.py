from typing import Literal


ChannelDecision = Literal["average", "fallback_a", "fallback_b", "invalid"]


def decide_channel(
    has_a: bool,
    has_b: bool,
    degraded: bool = False,
) -> ChannelDecision:
    """Choose how the redundant sensor channels should be consumed."""
    if has_a and has_b:
        return "invalid" if degraded else "average"
    if has_a:
        return "fallback_a"
    if has_b:
        return "fallback_b"
    return "invalid"
