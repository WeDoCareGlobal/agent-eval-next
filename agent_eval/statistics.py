"""Statistical comparison utilities for AgentEval.

Implements Welch's t-test (unpaired, unequal variance) for comparing two
independent groups of measurements, e.g., agent A's latencies vs agent B's.

A two-sided p-value is computed from the t-distribution. If p < alpha
(default 0.05), the null hypothesis (equal means) is rejected: the observed
difference is statistically significant.

Reference: Welch, B. L. (1947). "The generalization of Student's problem when
several different population variances are involved". Biometrika.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence


class StatisticalError(RuntimeError):
    """Raised for invalid inputs to statistical functions."""


def mean(values: Iterable[float]) -> float:
    """Compute the arithmetic mean of a sequence of numbers."""
    vals = list(values)
    if not vals:
        raise StatisticalError("cannot compute mean of empty sequence")
    return sum(vals) / len(vals)


def variance(values: Iterable[float], ddof: int = 1) -> float:
    """Compute the sample variance (unbiased, ddof=1)."""
    vals = list(values)
    n = len(vals)
    if n < 2:
        raise StatisticalError("variance requires at least 2 observations")
    m = mean(vals)
    return sum((x - m) ** 2 for x in vals) / (n - ddof)


def welch_ttest(
    sample1: Iterable[float],
    sample2: Iterable[float],
    alpha: float = 0.05,
) -> dict[str, object]:
    """Perform Welch's t-test on two independent samples.

    Returns a dict with:
        t_statistic: the computed t-value
        df: Welch-Satterthwaite degrees of freedom
        p_value: two-tailed p-value
        significant: bool (p < alpha)
        mean1, mean2: group means
        se: standard error of the difference
        n1, n2: group sizes
    """
    s1 = list(sample1)
    s2 = list(sample2)
    n1, n2 = len(s1), len(s2)
    if n1 < 2 or n2 < 2:
        raise StatisticalError("Welch's t-test requires at least 2 observations per group")

    m1, m2 = mean(s1), mean(s2)
    v1, v2 = variance(s1), variance(s2)

    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        # Both groups have zero variance; t-statistic is undefined.
        # If means differ, the difference is trivially significant.
        t = math.inf if m1 != m2 else 0.0
        return {
            "t_statistic": t,
            "df": 1.0,
            "p_value": 0.0 if m1 != m2 else 1.0,
            "significant": m1 != m2,
            "mean1": m1,
            "mean2": m2,
            "se": 0.0,
            "n1": n1,
            "n2": n2,
        }

    t = (m1 - m2) / se

    # Welch-Satterthwaite degrees of freedom
    num = (v1 / n1 + v2 / n2) ** 2
    denom = ((v1 / n1) ** 2) / (n1 - 1) + ((v2 / n2) ** 2) / (n2 - 1)
    df = num / denom if denom > 0 else 1.0

    p = _two_tailed_p_value(t, df)

    return {
        "t_statistic": t,
        "df": df,
        "p_value": p,
        "significant": p < alpha,
        "mean1": m1,
        "mean2": m2,
        "se": se,
        "n1": n1,
        "n2": n2,
    }


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    max_iter = 200
    eps = 3.0e-14
    fp_min = 1.0e-30

    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fp_min:
        d = fp_min
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fp_min:
            d = fp_min
        c = 1.0 + aa / c
        if abs(c) < fp_min:
            c = fp_min
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fp_min:
            d = fp_min
        c = 1.0 + aa / c
        if abs(c) < fp_min:
            c = fp_min
        d = 1.0 / d
        del_ = d * c
        h *= del_
        if abs(del_ - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    # Use the relation: I_x(a,b) = 1 - I_(1-x)(b,a) for x > (a+1)/(a+b+2)
    if x > (a + 1.0) / (a + b + 2.0):
        return 1.0 - _betai(b, a, 1.0 - x)
    # Use the continued fraction (Lentz's method)
    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    front = math.exp(ln_beta) / a
    return front * _betacf(a, b, x)


def _t_sf(t: float, df: float) -> float:
    """Survival function (1 - CDF) of Student's t-distribution."""
    x = df / (df + t * t)
    # I_{x}(df/2, 1/2) = 1 - CDF
    # For two-tailed, we want 2 * survival
    ib = _betai(df / 2.0, 0.5, x)
    return ib  # survival = I_{x}(df/2, 1/2)


def _two_tailed_p_value(t: float, df: float) -> float:
    """Compute the two-tailed p-value for a t-statistic."""
    if t == 0.0:
        return 1.0
    abs_t = abs(t)
    # p = 2 * survival(f(t, df))
    sf = _t_sf(abs_t, df)
    return min(2.0 * sf, 1.0)


if __name__ == "__main__":
    # Quick smoke test: two groups with different means
    g1 = [100.0, 102.0, 98.0, 101.0, 99.0]
    g2 = [160.0, 163.0, 158.0, 161.0, 159.0]
    result = welch_ttest(g1, g2, alpha=0.05)
    print("t =", result["t_statistic"])
    print("df =", result["df"])
    print("p =", result["p_value"])
    print("significant =", result["significant"])
