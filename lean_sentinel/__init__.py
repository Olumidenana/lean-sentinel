"""
LeanSentinel: Autonomous AI Agent Supervisor & Static Analysis Guardrails
for QuantConnect LEAN Algorithmic Trading Engines.
"""

__version__ = "1.0.0"
__author__ = "Olumide (QuantConnect Candidate)"
__license__ = "Apache-2.0"

from lean_sentinel.linter.analyzer import LeanASTAnalyzer
from lean_sentinel.statistics.dsr import calculate_dsr, haircut_sharpe_ratio
from lean_sentinel.synthesizer.generator import LeanFrameworkSynthesizer

__all__ = [
    "LeanASTAnalyzer",
    "calculate_dsr",
    "haircut_sharpe_ratio",
    "LeanFrameworkSynthesizer",
]
