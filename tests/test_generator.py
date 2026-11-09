"""
Unit tests for Framework Synthesizer and Auto-Remediation.
"""

from lean_sentinel.synthesizer.generator import LeanFrameworkSynthesizer
from lean_sentinel.linter.analyzer import LeanASTAnalyzer


def test_framework_synthesizer_generates_valid_code():
    code = LeanFrameworkSynthesizer.generate(strategy_type="momentum", symbols=["SPY", "QQQ"])
    assert "class InstitutionalMomentumAlgorithm(QCAlgorithm):" in code
    assert "AddAlpha" in code
    assert "SetPortfolioConstruction" in code
    assert "SetExecution" in code
    assert "AddRiskManagement" in code

    analyzer = LeanASTAnalyzer()
    res = analyzer.analyze_source(code)
    assert res.is_valid_python is True
    assert res.readiness_score >= 85


def test_auto_remediate_injects_guards():
    vulnerable = """
class Test(QCAlgorithm):
    def Initialize(self):
        self.SetWarmUp(30)
    def OnData(self, data):
        self.MarketOrder("AAPL", 10)
"""
    fixed = LeanFrameworkSynthesizer.sanitize_monolithic(vulnerable)
    assert "if self.IsWarmingUp:" in fixed
    assert "AddRiskManagement" in fixed
