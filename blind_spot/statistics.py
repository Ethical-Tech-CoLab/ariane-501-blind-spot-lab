"""Binomial calculations conditional on an explicitly chosen test distribution."""

import math

from .model import finite_number


def positive_count(n: int) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("Sample count must be a positive integer")


def probability(p: float) -> None:
    finite_number("probability", p)
    if not 0 <= p <= 1:
        raise ValueError("Probability must be in [0, 1]")


def detection_probability(p: float, n: int) -> float:
    probability(p)
    positive_count(n)
    return 1.0 if p == 1 else -math.expm1(n * math.log1p(-p))


def tests_for_detection(p: float, confidence: float = 0.95) -> int | None:
    probability(p)
    probability(confidence)
    if not 0 < confidence < 1:
        raise ValueError("Confidence must be strictly between zero and one")
    if p == 0:
        return None
    if p == 1:
        return 1
    return math.ceil(math.log1p(-confidence) / math.log1p(-p))


def zero_failure_upper(n: int, alpha: float = 0.05) -> float:
    positive_count(n)
    probability(alpha)
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be strictly between zero and one")
    return -math.expm1(math.log(alpha) / n)


def wilson_interval(k: int, n: int) -> tuple[float, float]:
    positive_count(n)
    if isinstance(k, bool) or not isinstance(k, int) or not 0 <= k <= n:
        raise ValueError("Success count must be an integer in [0, n]")
    z = 1.959963984540054
    p = k / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)
