"""
Golden-value tests for eval/metrics.py.

All expected values are hand-checked. These tests must pass in CI without any
API keys (they only exercise pure Python arithmetic).
"""

import math
import pytest

from eval.metrics import wilson_ci, raw_agreement, cohen_kappa, refusal_rate


# ---------------------------------------------------------------------------
# wilson_ci golden values
# Hand-checked via: https://www.wolframalpha.com/input?i=wilson+score+interval
# ---------------------------------------------------------------------------

class TestWilsonCI:
    def test_zero_successes(self):
        lo, hi = wilson_ci(0, 10)
        assert lo == pytest.approx(0.0, abs=1e-6)
        assert hi == pytest.approx(0.2775, abs=1e-3)

    def test_all_successes(self):
        lo, hi = wilson_ci(10, 10)
        assert lo == pytest.approx(0.7225, abs=1e-3)
        assert hi == pytest.approx(1.0, abs=1e-6)

    def test_half_successes(self):
        # k=5, n=10: classic midpoint; hand-verified
        lo, hi = wilson_ci(5, 10)
        assert lo == pytest.approx(0.2366, abs=1e-3)
        assert hi == pytest.approx(0.7634, abs=1e-3)

    def test_bounds_within_01(self):
        for k, n in [(0, 1), (1, 1), (3, 7), (99, 100)]:
            lo, hi = wilson_ci(k, n)
            assert 0.0 <= lo <= hi <= 1.0

    def test_n_zero(self):
        lo, hi = wilson_ci(0, 0)
        assert lo == 0.0 and hi == 1.0

    def test_small_n_high_k(self):
        # k=1, n=3: computed from the standard Wilson formula with z=1.96
        lo, hi = wilson_ci(1, 3)
        assert lo == pytest.approx(0.0615, abs=1e-3)
        assert hi == pytest.approx(0.7923, abs=1e-3)

    def test_large_n_convergence(self):
        # For large n, Wilson ≈ normal interval; midpoint ≈ p_hat
        lo, hi = wilson_ci(500, 1000)
        midpoint = (lo + hi) / 2
        assert midpoint == pytest.approx(0.5, abs=0.01)
        # Width should be ~2 * 1.96 * sqrt(0.25/1000) ≈ 0.062
        width = hi - lo
        assert width == pytest.approx(0.062, abs=0.005)


# ---------------------------------------------------------------------------
# raw_agreement golden values
# ---------------------------------------------------------------------------

class TestRawAgreement:
    def test_perfect_agreement(self):
        a = ["PASS", "PASS", "FAIL"]
        b = ["PASS", "PASS", "FAIL"]
        assert raw_agreement(a, b) == pytest.approx(1.0)

    def test_zero_agreement(self):
        a = ["PASS", "PASS"]
        b = ["FAIL", "FAIL"]
        assert raw_agreement(a, b) == pytest.approx(0.0)

    def test_partial_agreement(self):
        a = ["PASS", "FAIL", "PASS", "FAIL"]
        b = ["PASS", "PASS", "FAIL", "FAIL"]
        # 2 of 4 agree → 0.5
        assert raw_agreement(a, b) == pytest.approx(0.5)

    def test_empty_raises(self):
        # Empty is nan (no error raised; caller's responsibility)
        result = raw_agreement([], [])
        assert math.isnan(result)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            raw_agreement(["PASS"], ["PASS", "FAIL"])


# ---------------------------------------------------------------------------
# cohen_kappa golden values
# Hand-verified with formula on paper.
# ---------------------------------------------------------------------------

class TestCohenKappa:
    def test_perfect_agreement_binary(self):
        a = ["PASS", "FAIL", "PASS", "FAIL"]
        b = ["PASS", "FAIL", "PASS", "FAIL"]
        assert cohen_kappa(a, b) == pytest.approx(1.0)

    def test_zero_beyond_chance(self):
        # κ = 0 when P_o = P_e
        # With 50/50 split and cross-agreement: P_o = 0.5, P_e = 0.5 → κ = 0
        a = ["PASS", "PASS", "FAIL", "FAIL"]
        b = ["PASS", "FAIL", "PASS", "FAIL"]
        kappa = cohen_kappa(a, b)
        assert kappa == pytest.approx(0.0, abs=1e-9)

    def test_known_value_three_class(self):
        # 5 items; rater A: [A, A, B, B, C], rater B: [A, B, B, C, C]
        # Agreed items: index 0 (A,A), index 2 (B,B), index 4 (C,C) → P_o = 3/5 = 0.6
        # P(A): a=2/5, b=1/5 → 2/25
        # P(B): a=2/5, b=2/5 → 4/25
        # P(C): a=1/5, b=2/5 → 2/25
        # P_e = (2+4+2)/25 = 8/25 = 0.32
        # κ = (0.6 - 0.32) / (1 - 0.32) = 0.28 / 0.68 ≈ 0.4118
        a = ["A", "A", "B", "B", "C"]
        b = ["A", "B", "B", "C", "C"]
        assert cohen_kappa(a, b) == pytest.approx(0.28 / 0.68, abs=1e-9)

    def test_single_label_returns_nan(self):
        a = ["PASS", "PASS", "PASS"]
        b = ["PASS", "PASS", "PASS"]
        # P_e = 1 → nan
        result = cohen_kappa(a, b)
        assert math.isnan(result)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            cohen_kappa(["PASS"], ["PASS", "FAIL"])


# ---------------------------------------------------------------------------
# refusal_rate golden values
# ---------------------------------------------------------------------------

class TestRefusalRate:
    def test_all_compliant(self):
        rt = ["full_compliance"] * 10
        r = refusal_rate(rt)
        assert r["n"] == 10
        assert r["k"] == 0
        assert r["rate"] == pytest.approx(0.0)
        lo, hi = r["ci_lower"], r["ci_upper"]
        assert lo == pytest.approx(0.0, abs=1e-6)
        assert hi == pytest.approx(0.2775, abs=1e-3)

    def test_all_refused(self):
        rt = ["full_refusal"] * 5
        r = refusal_rate(rt)
        assert r["n"] == 5
        assert r["k"] == 5
        assert r["rate"] == pytest.approx(1.0)

    def test_partial_counts_as_refusal_by_default(self):
        rt = ["full_compliance", "partial_compliance", "full_refusal"]
        r = refusal_rate(rt)
        assert r["k"] == 2  # partial + full refusal

    def test_partial_excluded_when_flag_false(self):
        rt = ["full_compliance", "partial_compliance", "full_refusal"]
        r = refusal_rate(rt, count_partial=False)
        assert r["k"] == 1  # only full_refusal

    def test_empty(self):
        r = refusal_rate([])
        assert r["n"] == 0
        assert math.isnan(r["rate"])
        assert r["ci_lower"] == 0.0
        assert r["ci_upper"] == 1.0
