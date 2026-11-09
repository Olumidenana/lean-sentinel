"""
Institutional Quantitative Performance Metrics Engine.
Computes risk-adjusted performance, drawdown dynamics, and tail risks.
"""

import math
from typing import List, Dict, Any, Union
import numpy as np


class PerformanceMetrics:
    @staticmethod
    def calculate_all(returns: Union[List[float], np.ndarray], risk_free_rate: float = 0.02, periods_per_year: int = 252) -> Dict[str, Any]:
        ret = np.array(returns, dtype=float)
        if len(ret) < 2:
            return {"error": "Insufficient return periods to compute statistics."}

        # Filter out NaN or Infs
        ret = ret[np.isfinite(ret)]
        n = len(ret)
        if n < 2:
            return {"error": "Insufficient valid return samples."}

        total_return = float(np.prod(1.0 + ret) - 1.0)
        years = n / periods_per_year
        annualized_return = float((1.0 + total_return) ** (1.0 / max(years, 0.001)) - 1.0) if total_return > -1.0 else -1.0

        daily_rf = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
        excess_returns = ret - daily_rf

        mean_excess = np.mean(excess_returns)
        std_dev = np.std(ret, ddof=1)
        annualized_vol = float(std_dev * math.sqrt(periods_per_year)) if std_dev > 0 else 0.0

        # Sharpe Ratio
        sharpe = float((mean_excess / std_dev) * math.sqrt(periods_per_year)) if std_dev > 0 else 0.0

        # Downside Deviation & Sortino
        downside_diff = np.minimum(0.0, excess_returns)
        downside_std = np.sqrt(np.mean(downside_diff ** 2))
        sortino = float((mean_excess / downside_std) * math.sqrt(periods_per_year)) if downside_std > 0 else 0.0

        # Drawdowns
        cum_equity = np.cumprod(1.0 + ret)
        running_max = np.maximum.accumulate(cum_equity)
        drawdowns = (cum_equity - running_max) / running_max
        max_drawdown = float(np.min(drawdowns))  # negative float

        # Max Drawdown Duration
        in_drawdown = drawdowns < 0
        max_dd_duration = 0
        cur_duration = 0
        for is_dd in in_drawdown:
            if is_dd:
                cur_duration += 1
                if cur_duration > max_dd_duration:
                    max_dd_duration = cur_duration
            else:
                cur_duration = 0

        # Calmar Ratio
        calmar = float(annualized_return / abs(max_drawdown)) if abs(max_drawdown) > 0.0001 else 0.0

        # Win Rate & Profit Factor
        winning_trades = ret[ret > 0]
        losing_trades = ret[ret < 0]
        win_rate = float(len(winning_trades) / n) if n > 0 else 0.0

        gross_profit = float(np.sum(winning_trades)) if len(winning_trades) > 0 else 0.0
        gross_loss = float(abs(np.sum(losing_trades))) if len(losing_trades) > 0 else 0.0
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

        # Skewness & Kurtosis
        skewness = float(np.mean(((ret - np.mean(ret)) / (std_dev if std_dev > 0 else 1.0)) ** 3))
        kurtosis = float(np.mean(((ret - np.mean(ret)) / (std_dev if std_dev > 0 else 1.0)) ** 4))

        # Value at Risk (VaR 95%) and Conditional VaR (CVaR / Expected Shortfall 95%)
        sorted_returns = np.sort(ret)
        var_index = int(0.05 * n)
        var_95 = float(-sorted_returns[var_index]) if n >= 20 else float(-np.percentile(ret, 5))
        cvar_95 = float(-np.mean(sorted_returns[:max(1, var_index)]))

        return {
            "sample_periods": int(n),
            "total_return": round(total_return, 4),
            "annualized_return": round(annualized_return, 4),
            "annualized_volatility": round(annualized_vol, 4),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "calmar_ratio": round(calmar, 3),
            "max_drawdown": round(max_drawdown, 4),
            "max_drawdown_duration_bars": int(max_dd_duration),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 2),
            "skewness": round(skewness, 3),
            "kurtosis": round(kurtosis, 3),
            "var_95": round(var_95, 4),
            "cvar_95": round(cvar_95, 4),
        }
