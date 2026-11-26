from collections.abc import Sequence
from math import sqrt


def euclidean_difference(first: Sequence[float], second: Sequence[float]) -> float:
    """Return the Euclidean distance between two equally sized vectors."""
    if len(first) != len(second):
        raise ValueError("Vectors must have the same dimension")
    return sqrt(sum((left - right) ** 2 for left, right in zip(first, second)))
