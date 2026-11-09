"""
LeanSentinel: End-to-End Interactive Showcase.
Demonstrates:
1. Static Analysis & Anti-Hallucination Audit of a flawed AI algorithm
2. Auto-Remediation into a compliant script
3. Synthesizing a 5-Component Algorithm Framework
4. Calculating Deflated Sharpe Ratio (DSR) & Overfitting Risk
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lean_sentinel.linter.analyzer import LeanASTAnalyzer
from lean_sentinel.linter.reporter import LeanReporter
from lean_sentinel.synthesizer.generator import LeanFrameworkSynthesizer
from lean_sentinel.statistics.dsr import calculate_dsr
from lean_sentinel.statistics.metrics import PerformanceMetrics
import numpy as np


def run_demo():
    print("=" * 76)
    print("  🛡️  LEANSENTINEL: QUANTCONNECT AI AGENT SUPERVISOR & STATIC LINTER")
    print("  Engineered for Jared Broad & QuantConnect MCP Agentic Architecture")
    print("=" * 76)

    # 1. Audit Flawed Code
    print("\n[STEP 1] Auditing AI-Generated Vulnerable Algorithm...")
    vulnerable_path = Path(__file__).parent / "examples" / "vulnerable_algorithm.py"
    code = vulnerable_path.read_text(encoding="utf-8")

    analyzer = LeanASTAnalyzer()
    res = analyzer.analyze_source(code, filename="vulnerable_algorithm.py")
    print(LeanReporter.to_cli_text(res))

    # 2. Auto-Remediation
    print("\n[STEP 2] Running Automated Surgical Remediation...")
    fixed_code = LeanFrameworkSynthesizer.sanitize_monolithic(code)
    fixed_res = analyzer.analyze_source(fixed_code, filename="remediated_algorithm.py")
    print(f"  ✓ Code Remediated! New Readiness Score: {fixed_res.readiness_score}/100 (Grade: {fixed_res.grade})")
    print(f"  ✓ Remaining Violations: {fixed_res.total_findings} (Down from {res.total_findings})")

    # 3. 5-Component Framework Synthesis
    print("\n[STEP 3] Synthesizing Institutional 5-Component LEAN Framework...")
    framework_code = LeanFrameworkSynthesizer.generate(
        strategy_type="momentum",
        symbols=["SPY", "QQQ", "IWM", "GLD", "TLT"]
    )
    framework_res = analyzer.analyze_source(framework_code, filename="institutional_framework.py")
    print(f"  ✓ Framework Generated! Readiness Score: {framework_res.readiness_score}/100 (Grade: {framework_res.grade})")
    print("  ✓ Architecture: Coarse Universe + Momentum Alpha + Insight Weighting + Immediate Exec + MaxDD Risk Model")

    # 4. Statistical Rigor & Deflated Sharpe Ratio (DSR)
    print("\n[STEP 4] Evaluating Overfitting via Deflated Sharpe Ratio (Lopez de Prado)...")
    np.random.seed(42)
    daily_returns = list(np.random.normal(0.0007, 0.012, 252))
    perf = PerformanceMetrics.calculate_all(daily_returns)
    observed_sr = perf["sharpe_ratio"]

    # Compare 1 trial vs 50 trials (simulating an AI agent that ran 50 prompt iterations)
    dsr_1 = calculate_dsr(observed_sharpe=observed_sr, returns=daily_returns, n_trials=1)
    dsr_50 = calculate_dsr(observed_sharpe=observed_sr, returns=daily_returns, n_trials=50)

    print(f"  Observed Sharpe Ratio:          {observed_sr}")
    print(f"  Annualized Volatility:          {perf['annualized_volatility'] * 100:.1f}%")
    print(f"  Max Drawdown:                   {perf['max_drawdown'] * 100:.1f}%")
    print("-" * 76)
    print(f"  [1 Trial (Single Test)]:        DSR Prob = {dsr_1['dsr_probability']*100:.1f}% | Risk: {dsr_1['overfitting_risk']}")
    print(f"  [50 Trials (AI Prompt Snooping)]: DSR Prob = {dsr_50['dsr_probability']*100:.1f}% | Risk: {dsr_50['overfitting_risk']}")
    print(f"  Haircut Sharpe Ratio (Adjusted): {dsr_50['haircut_sharpe_ratio']}")
    print(f"  Expected Max Null Sharpe:        {dsr_50['expected_max_null_sharpe']}")

    print("\n" + "=" * 76)
    print("  ✨ DEMO COMPLETED SUCCESSFULLY!")
    print("  To launch the Interactive Studio, run: python -m lean_sentinel.cli serve")
    print("=" * 76)


if __name__ == "__main__":
    run_demo()
