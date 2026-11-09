"""
Deflated Sharpe Ratio (DSR) & Haircut Sharpe Ratio Engine.
Based on Marcos Lopez de Prado (2014) and Campbell Harvey (2015).
Protects QuantConnect quants and AI agents against false discovery and curve-fitting.
"""

import math
from typing import Dict, Any, Union, List
import numpy as np


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function (CDF)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def expected_max_sharpe(n_trials: int, var_sharpe: float = 0.5) -> float:
    """
    Computes expected maximum Sharpe ratio under the null hypothesis
    of zero true alpha across N independent trials (Euler-Mascheroni approximation).
    """
    if n_trials <= 1:
        return 0.0

    gamma = 0.5772156649  # Euler-Mascheroni constant
    z = math.sqrt(2.0 * math.log(n_trials))
    e_max = (1.0 - gamma / z) * z + (math.pi**2 / (12.0 * z))
    return float(math.sqrt(var_sharpe) * e_max)


def calculate_dsr(
    observed_sharpe: float,
    returns: Union[List[float], np.ndarray],
    n_trials: int = 20,
    var_sharpe: float = 0.5,
    periods_per_year: int = 252,
) -> Dict[str, Any]:
    """
    Calculate Deflated Sharpe Ratio (DSR).
    Returns DSR probability (0 to 1.0). A DSR > 0.95 indicates genuine statistical significance.
    """
    ret = np.array(returns, dtype=float)
    ret = ret[np.isfinite(ret)]
    t = len(ret)

    if t < 10:
        return {
            "error": "Sample size T must be at least 10 bars.",
            "dsr_probability": 0.0,
            "is_significant": False,
        }

    std_dev = np.std(ret, ddof=1)
    if std_dev <= 0:
        return {
            "error": "Return series has zero volatility.",
            "dsr_probability": 0.0,
            "is_significant": False,
        }

    # Standardized moments
    mean = np.mean(ret)
    skewness = float(np.mean(((ret - mean) / std_dev) ** 3))
    kurtosis = float(np.mean(((ret - mean) / std_dev) ** 4))

    # Expected max Sharpe under data snooping
    sr_star = expected_max_sharpe(n_trials, var_sharpe)

    # Standard error under non-normality
    # SE = sqrt((1 - skew*SR + ((kurt - 1)/4)*SR^2) / (T - 1))
    sr = observed_sharpe / math.sqrt(periods_per_year)  # convert to per-period scale
    sr_star_period = sr_star / math.sqrt(periods_per_year)

    var_term = 1.0 - (skewness * sr) + (((kurtosis - 1.0) / 4.0) * (sr**2))
    var_term = max(0.00001, var_term)
    se = math.sqrt(var_term / (t - 1.0))

    z_stat = (sr - sr_star_period) / se
    dsr_prob = norm_cdf(z_stat)

    # Haircut Sharpe: Penalize Sharpe based on trial count N
    haircut_factor = 1.0 / (1.0 + 0.15 * math.log(max(1, n_trials)))
    haircut_sr = observed_sharpe * haircut_factor

    return {
        "observed_sharpe": round(observed_sharpe, 3),
        "expected_max_null_sharpe": round(sr_star, 3),
        "n_trials_evaluated": int(n_trials),
        "sample_size_bars": int(t),
        "skewness": round(skewness, 3),
        "kurtosis": round(kurtosis, 3),
        "z_statistic": round(z_stat, 3),
        "dsr_probability": round(dsr_prob, 4),
        "is_statistically_significant": bool(dsr_prob >= 0.95),
        "overfitting_risk": "LOW" if dsr_prob >= 0.95 else ("MODERATE" if dsr_prob >= 0.70 else "HIGH"),
        "haircut_sharpe_ratio": round(haircut_sr, 3),
    }


def haircut_sharpe_ratio(observed_sharpe: float, n_trials: int = 1) -> float:
    """Quick haircut adjustment for exploratory multiple backtesting."""
    if n_trials <= 1:
        return observed_sharpe
    factor = 1.0 / (1.0 + 0.12 * math.log(n_trials))
    return round(observed_sharpe * factor, 3)
