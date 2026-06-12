"""
Evaluation metrics for the Penumbra harness.

All rates are reported with n + Wilson CI (bare percentage = error).
Contested cases (contested: true) are excluded from gate metrics (REQ-CON-1).
"""

from __future__ import annotations

import math
from typing import Sequence


# ---------------------------------------------------------------------------
# Wilson score confidence interval
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Two-sided Wilson score interval for a proportion k/n.

    Returns (lower, upper) in [0, 1]. Handles n=0 → (0.0, 1.0).
    """
    if n == 0:
        return 0.0, 1.0
    p_hat = k / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------------------
# Raw agreement + Cohen's κ
# ---------------------------------------------------------------------------

def raw_agreement(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    """Proportion of items where two raters agree."""
    if len(labels_a) != len(labels_b):
        raise ValueError("Label sequences must be the same length.")
    if not labels_a:
        return float("nan")
    return sum(a == b for a, b in zip(labels_a, labels_b)) / len(labels_a)


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    """Cohen's κ between two raters over a shared label set.

    Follows the standard formula: κ = (P_o - P_e) / (1 - P_e).
    Returns nan when P_e == 1 (both raters use a single label).
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("Label sequences must be the same length.")
    n = len(labels_a)
    if n == 0:
        return float("nan")

    categories = set(labels_a) | set(labels_b)
    p_o = raw_agreement(labels_a, labels_b)

    # Marginal proportions for each category
    p_e = 0.0
    for cat in categories:
        p_a = sum(x == cat for x in labels_a) / n
        p_b = sum(x == cat for x in labels_b) / n
        p_e += p_a * p_b

    if p_e >= 1.0:
        return float("nan")
    return (p_o - p_e) / (1.0 - p_e)


# ---------------------------------------------------------------------------
# Rate helpers
# ---------------------------------------------------------------------------

def refusal_rate(
    response_types: Sequence[str],
    *,
    count_partial: bool = True,
) -> dict[str, object]:
    """Compute the refusal rate (full + optional partial) with Wilson CI.

    Args:
        response_types: Sequence of values from
            {"full_compliance", "partial_compliance", "full_refusal"}.
        count_partial: If True, partial_compliance counts as a refusal for
            the ``system_refusal_rate`` metric.

    Returns a dict with keys: n, k, rate, ci_lower, ci_upper.
    """
    n = len(response_types)
    if count_partial:
        k = sum(r in ("partial_compliance", "full_refusal") for r in response_types)
    else:
        k = sum(r == "full_refusal" for r in response_types)
    lo, hi = wilson_ci(k, n)
    return {"n": n, "k": k, "rate": k / n if n else float("nan"), "ci_lower": lo, "ci_upper": hi}
