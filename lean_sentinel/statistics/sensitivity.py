"""
Monte Carlo & Execution Slippage Sensitivity Testing.
Simulates distribution of outcomes under real-world slippage and execution jitter.
"""

from typing import List, Dict, Any, Union
import numpy as np


class SensitivityEngine:
    @staticmethod
    def run_monte_carlo(
        returns: Union[List[float], np.ndarray],
        num_simulations: int = 500,
        horizon_bars: int = 252,
        slippage_bps: float = 5.0,  # 5 bps slippage per period
    ) -> Dict[str, Any]:
        ret = np.array(returns, dtype=float)
        ret = ret[np.isfinite(ret)]
        if len(ret) < 10:
            return {"error": "Need at least 10 return periods."}

        # Apply slippage friction: basis points converted to decimal
        friction = (slippage_bps / 10000.0)
        net_returns = ret - friction

        # Bootstrap resample paths
        n = len(net_returns)
        simulated_finals = []
        simulated_max_dds = []

        for _ in range(num_simulations):
            sample_idx = np.random.choice(n, size=horizon_bars, replace=True)
            sampled_ret = net_returns[sample_idx]
            cum_path = np.cumprod(1.0 + sampled_ret)

            simulated_finals.append(cum_path[-1] - 1.0)

            # Max drawdown for path
            running_peak = np.maximum.accumulate(cum_path)
            dd = (cum_path - running_peak) / running_peak
            simulated_max_dds.append(np.min(dd))

        simulated_finals = np.array(simulated_finals)
        simulated_max_dds = np.array(simulated_max_dds)

        return {
            "num_simulations": num_simulations,
            "horizon_bars": horizon_bars,
            "applied_slippage_bps": slippage_bps,
            "median_projected_return": round(float(np.median(simulated_finals)), 4),
            "p5_bear_case_return": round(float(np.percentile(simulated_finals, 5)), 4),
            "p95_bull_case_return": round(float(np.percentile(simulated_finals, 95)), 4),
            "probability_of_profit": round(float(np.mean(simulated_finals > 0)), 4),
            "worst_case_drawdown_p95": round(float(np.percentile(simulated_max_dds, 5)), 4),
            "median_drawdown": round(float(np.median(simulated_max_dds)), 4),
            "robustness_score": int(round(float(np.mean(simulated_finals > 0) * 100))),
        }
