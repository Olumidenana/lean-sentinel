"""
Unit tests for LeanSentinel AST Linter.
"""

from pathlib import Path
from lean_sentinel.linter.analyzer import LeanASTAnalyzer
from lean_sentinel.linter.rules import Severity


def test_vulnerable_algorithm_detection():
    vulnerable_code = """
class MyAlgo(QCAlgorithm):
    def Initialize(self):
        self.AddEquity("SPY")
        self.ema = self.EMA("SPY", 14)
        self.SetWarmUp(30)

    def OnData(self, data):
        val = self.ema.Current.Value
        if data["SPY"].Close > val:
            self.MarketOrder("SPY", 100)
"""
    analyzer = LeanASTAnalyzer()
    res = analyzer.analyze_source(vulnerable_code)

    assert res.is_valid_python is True
    assert res.readiness_score < 70
    assert res.grade in ("D", "F")
    rule_ids = [f.rule_id for f in res.findings]
    assert "QC-003" in rule_ids  # Missing IsWarmingUp
    assert "QC-002" in rule_ids  # Unchecked indicator
    assert "QC-004" in rule_ids  # MarketOrder
    assert "QC-007" in rule_ids  # Direct subscript
    assert "QC-006" in rule_ids  # Missing Resolution


def test_clean_algorithm_high_score():
    clean_code = """
class CleanAlgo(QCAlgorithm):
    def Initialize(self):
        self.AddEquity("SPY", Resolution.Daily)
        self.sma = self.SMA("SPY", 20, Resolution.Daily)
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))
        self.SetWarmUp(timedelta(days=20))

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return
        if not data.ContainsKey("SPY") or data["SPY"] is None:
            return
        if not self.sma.IsReady:
            return
        if data["SPY"].Close > self.sma.Current.Value:
            self.SetHoldings("SPY", 1.0)
"""
    analyzer = LeanASTAnalyzer()
    res = analyzer.analyze_source(clean_code)

    assert res.is_valid_python is True
    assert res.readiness_score >= 80
    assert res.critical_count == 0


def test_syntax_error_handling():
    broken_code = "class Broken(QCAlgorithm):\n    def Initialize(self\n        pass"
    analyzer = LeanASTAnalyzer()
    res = analyzer.analyze_source(broken_code)

    assert res.is_valid_python is False
    assert res.readiness_score == 0
    assert res.grade == "F"
    assert res.findings[0].rule_id == "SYNTAX-001"
