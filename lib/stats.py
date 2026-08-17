"""
Statistical inference helpers.

The project's central claim is that a proportion changed — the share of
matches won at home, and the share of bookings going to away teams. A
difference between two proportions is only meaningful alongside its
uncertainty, so these functions supply confidence intervals and tests
for every headline figure the application reports.

Implemented directly on top of NumPy rather than SciPy: the deployment
environment installs only what `requirements.txt` names, and adding a
dependency for two formulas is a poor trade.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# 95% two-sided normal critical value.
Z95 = 1.959963984540054


def _normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution, via the error function."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# --------------------------------------------------------------------------
# One proportion
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Proportion:
    successes: int
    n: int
    estimate: float      # percentage points
    low: float           # lower confidence bound, percentage points
    high: float          # upper confidence bound, percentage points

    @property
    def margin(self) -> float:
        """Half-width of the interval, in percentage points."""
        return (self.high - self.low) / 2.0


def wilson_interval(successes: int, n: int, z: float = Z95) -> Proportion:
    """
    Wilson score interval for a binomial proportion, returned as percentages.

    The Wilson interval is used in preference to the textbook normal
    approximation because it stays inside [0, 1] and remains accurate for
    small samples — which matters here, since the empty-stadium window is
    short and some per-league subsets are modest.
    """
    if n <= 0:
        return Proportion(0, 0, float("nan"), float("nan"), float("nan"))

    p = successes / n
    denom = 1.0 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))

    return Proportion(
        successes=int(successes),
        n=int(n),
        estimate=p * 100.0,
        low=max(0.0, centre - half) * 100.0,
        high=min(1.0, centre + half) * 100.0,
    )


# --------------------------------------------------------------------------
# Difference between two proportions
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ProportionDiff:
    diff: float          # percentage points, group 1 minus group 2
    low: float           # confidence bounds on the difference
    high: float
    z: float
    p_value: float
    n1: int
    n2: int

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05

    def p_text(self) -> str:
        """A p-value formatted the way a report would print it."""
        if math.isnan(self.p_value):
            return "n/a"
        if self.p_value < 0.001:
            return "p < 0.001"
        return f"p = {self.p_value:.3f}"


def two_proportion_test(
    x1: int, n1: int, x2: int, n2: int, z: float = Z95
) -> ProportionDiff:
    """
    Two-sided test for a difference between two independent proportions,
    with a confidence interval on the difference.

    The test statistic uses the pooled proportion, as is standard for the
    null hypothesis of equality; the interval uses unpooled standard
    errors, since under the alternative the two proportions differ.
    """
    if n1 <= 0 or n2 <= 0:
        nan = float("nan")
        return ProportionDiff(nan, nan, nan, nan, nan, int(n1), int(n2))

    p1, p2 = x1 / n1, x2 / n2
    diff = p1 - p2

    pooled = (x1 + x2) / (n1 + n2)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    stat = diff / se_pooled if se_pooled > 0 else float("nan")
    p_value = 2 * (1 - _normal_cdf(abs(stat))) if se_pooled > 0 else float("nan")

    se_unpooled = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    half = z * se_unpooled

    return ProportionDiff(
        diff=diff * 100.0,
        low=(diff - half) * 100.0,
        high=(diff + half) * 100.0,
        z=stat,
        p_value=p_value,
        n1=int(n1),
        n2=int(n2),
    )


# --------------------------------------------------------------------------
# Difference between two means
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class MeanDiff:
    diff: float
    low: float
    high: float
    t: float
    p_value: float
    n1: int
    n2: int

    @property
    def significant(self) -> bool:
        return self.p_value < 0.05

    def p_text(self) -> str:
        if math.isnan(self.p_value):
            return "n/a"
        if self.p_value < 0.001:
            return "p < 0.001"
        return f"p = {self.p_value:.3f}"


def welch_test(a, b, z: float = Z95) -> MeanDiff:
    """
    Welch's test for a difference between two means, used for the booking
    gap, which is a count difference rather than a proportion.

    Welch rather than Student: the two groups differ greatly in size and
    there is no reason to assume equal variances. The normal
    approximation is used for the p-value, which is safe at these sample
    sizes (thousands of matches per group).
    """
    a = np.asarray(a, dtype="float64")
    b = np.asarray(b, dtype="float64")
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]

    n1, n2 = a.size, b.size
    if n1 < 2 or n2 < 2:
        nan = float("nan")
        return MeanDiff(nan, nan, nan, nan, nan, int(n1), int(n2))

    m1, m2 = float(a.mean()), float(b.mean())
    v1, v2 = float(a.var(ddof=1)), float(b.var(ddof=1))
    se = math.sqrt(v1 / n1 + v2 / n2)

    diff = m1 - m2
    stat = diff / se if se > 0 else float("nan")
    p_value = 2 * (1 - _normal_cdf(abs(stat))) if se > 0 else float("nan")

    return MeanDiff(
        diff=diff,
        low=diff - z * se,
        high=diff + z * se,
        t=stat,
        p_value=p_value,
        n1=n1,
        n2=n2,
    )


# --------------------------------------------------------------------------
# Paired differences
# --------------------------------------------------------------------------

def paired_test(differences, z: float = Z95) -> MeanDiff:
    """
    One-sample test on a set of paired differences.

    Used for the within-club comparison: for every club that played in
    both periods, the change in its own home advantage. Pairing removes
    every fixed property of the club — its quality, its stadium, its
    league — so the comparison cannot be explained by a different mix of
    teams being present in the two periods.

    `n2` is reported as 0, since a paired test has a single sample.
    """
    d = np.asarray(differences, dtype="float64")
    d = d[~np.isnan(d)]
    n = d.size

    if n < 2:
        nan = float("nan")
        return MeanDiff(nan, nan, nan, nan, nan, int(n), 0)

    mean = float(d.mean())
    se = float(d.std(ddof=1)) / math.sqrt(n)
    stat = mean / se if se > 0 else float("nan")
    p_value = 2 * (1 - _normal_cdf(abs(stat))) if se > 0 else float("nan")

    return MeanDiff(
        diff=mean,
        low=mean - z * se,
        high=mean + z * se,
        t=stat,
        p_value=p_value,
        n1=n,
        n2=0,
    )
