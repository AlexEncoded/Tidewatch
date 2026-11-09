"""Shared value types for analytical confidence and environmental state."""

from typing import Literal


AnalysisConfidence = Literal["experimental", "insufficient_data"]
SeaState = Literal["unknown", "calm", "moderate", "rough"]
