"""
Unit tests for Institutional Quantitative Statistics and DSR.
"""

import numpy as np
from lean_sentinel.statistics.metrics import PerformanceMetrics
from lean_sentinel.statistics.dsr import calculate_dsr, expected_max_sharpe, haircut_sharpe_ratio
from lean_sentinel.statistics.sensitivity import SensitivityEngine


def test_performance_metrics_calculation():
    np.random.seed(42)
    # 252 daily returns with positive Sharpe
    returns = np.random.normal(0.0008, 0.01, 252)
    metrics = PerformanceMetrics.calculate_all(returns)

    assert "sharpe_ratio" in metrics
    assert metrics["sharpe_ratio"] > 0
    assert "sortino_ratio" in metrics
    assert "max_drawdown" in metrics
    assert metrics["max_drawdown"] <= 0
    assert 0 <= metrics["win_rate"] <= 1.0


def test_deflated_sharpe_ratio():
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.012, 252)

    # 1 trial vs 100 trials: DSR probability should penalize multiple testing
    dsr_single = calculate_dsr(observed_sharpe=2.0, returns=returns, n_trials=1)
    dsr_many = calculate_dsr(observed_sharpe=2.0, returns=returns, n_trials=100)

    assert dsr_single["dsr_probability"] > dsr_many["dsr_probability"]
    assert dsr_many["expected_max_null_sharpe"] > dsr_single["expected_max_null_sharpe"]
    assert dsr_many["haircut_sharpe_ratio"] < 2.0


def test_haircut_sharpe_ratio():
    sr = 2.0
    haircut_1 = haircut_sharpe_ratio(sr, n_trials=1)
    haircut_50 = haircut_sharpe_ratio(sr, n_trials=50)

    assert haircut_1 == sr
    assert haircut_50 < sr


def test_sensitivity_monte_carlo():
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.015, 252)
    res = SensitivityEngine.run_monte_carlo(returns, num_simulations=100, horizon_bars=100)

    assert "median_projected_return" in res
    assert "probability_of_profit" in res
    assert 0 <= res["probability_of_profit"] <= 1.0
