"""Gompertz-Makeham mortality:  mu(x) = a + b * exp(c * x)

alph * exp(beta * x) + lambda

`a` is extrinsic mortality (accidents, violence) and is flat with age.
`b * exp(c*x)` is senescence, doubling every ln(2)/c years - about 8 in
human populations.

Gompertz-Makeham does not model early mortality well, as mortality
rates are elevated in infancy and adolescence.
"""

import numpy as np

WEEKS_PER_YEAR: float = 365.2425 / 7
# options: 52 means we have rows land on birthdays.
# 365.2425 / 7 are "real" weeks, so 90 rows is 90 years, accounting for leap years.


class GompertzMakehamModel:
    def __init__(self, alph: float, beta: float, lamb: float):
        self.alph: float = alph
        self.beta: float = beta
        self.lamb: float = lamb

    def step_hazard(
        self, steps: np.ndarray[tuple[int], np.dtype[np.float64]], per_year: float = 1
    ):
        """P(die during step i | alive at its start), for steps of 1/W years.

        Exact integral of mu over each step, not a point evaluation.
        """
        alph: float = self.alph / per_year
        beta: float = self.beta / per_year
        lamb: float = self.lamb / per_year

        steps: np.ndarray[tuple[int], np.dtype[np.float64]] = np.asarray(steps, float)
        return -np.expm1(
            -(lamb + (alph / beta) * np.exp(beta * steps) * np.expm1(lamb))
        )  # tf?

    def fit(self, observed_qx, lo: int = 30, hi: int = 90, weights=None):
        """Fit alpha, beta, lambda to a slice of a life table's q(x).

        Grid-searches the Makeham term; for each candidate `lambda`, the other two
        fall out of an OLS of log(mu - lambda) on age, so there is no optimiser.
        Pass l(x) as `weights` so sparse old ages don't dominate.
        """
        ages = np.arange(lo, hi + 1, dtype=float)
        mu = -np.log1p(-np.clip(observed_qx[lo : hi + 1], 1e-12, 1 - 1e-12))
        w = (
            np.ones_like(ages)
            if weights is None
            else np.asarray(weights[lo : hi + 1], float)
        )

        best = None
        for a in np.r_[0.0, np.logspace(-6, np.log10(mu.min() * 0.999), 300)]:
            y = np.log(mu - a)
            c, log_b = np.polyfit(ages, y, 1, w=np.sqrt(w))
            residual = np.sum(w * (y - c * ages - log_b) ** 2)
            if best is None or residual < best[0]:
                # The regression targets the hazard integrated over a year, not
                # mu at exact age x; for the Gompertz term those differ by
                # (e^c - 1)/c, ~5%. Only the intercept needs it.
                best = (residual, a, np.exp(log_b) * c / np.expm1(c), c)
        return best[1:]

    def age_shift(self, hazard_ratio, c):
        """Years of ageing equivalent to a hazard ratio.

        Under Gompertz, multiplying the hazard by HR is exactly the same as
        aging forward by ln(HR)/c. This is where "smoking ages you ten years"
        comes from, and it is better behaved in the 90s than a flat multiplier.
        """
        return np.log(hazard_ratio) / c

    def survival(
        self,
        a,
        b,
        c,
        weeks_lived=0,
        n_weeks=90 * WEEKS_PER_YEAR,
        shift=0.0,
        per_year=WEEKS_PER_YEAR,
    ):
        """S[i] = P(alive at end of week i), conditioned on reaching `weeks_lived`.

        `shift` ages the senescent term forward - pass age_shift(HR, c). The
        Makeham term does not shift: being biologically older doesn't raise
        your car-crash risk.
        """
        hazard = self.step_hazard(
            np.arange(n_weeks), a, b * np.exp(c * shift), c, per_year
        )
        hazard[:weeks_lived] = 0.0
        return np.cumprod(1.0 - hazard)
