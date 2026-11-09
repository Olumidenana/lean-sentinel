"""
Rule catalog and definitions for QuantConnect LEAN Static Analysis.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(str, Enum):
    LOOKAHEAD_BIAS = "Lookahead Bias"
    EXECUTION_SAFETY = "Execution Safety"
    INDICATOR_WARMUP = "Indicator Warmup"
    ARCHITECTURE = "Framework Architecture"
    DATA_INTEGRITY = "Data Integrity"
    DEPRECATION = "API Modernity"


@dataclass
class RuleDefinition:
    id: str
    name: str
    severity: Severity
    category: Category
    description: str
    remediation: str


RULE_CATALOG = {
    "QC-001": RuleDefinition(
        id="QC-001",
        name="Lookahead Bias / Future Leakage",
        severity=Severity.CRITICAL,
        category=Category.LOOKAHEAD_BIAS,
        description="Accessing unshifted future bars, prospective close prices, or negative history offsets inside OnData.",
        remediation="Always ensure indicators are fed closed bars. In event-driven LEAN, rely on Slice data or History with lag to prevent future leakage.",
    ),
    "QC-002": RuleDefinition(
        id="QC-002",
        name="Unchecked Indicator Readiness",
        severity=Severity.HIGH,
        category=Category.INDICATOR_WARMUP,
        description="Reading indicator.Current.Value without first checking indicator.IsReady.",
        remediation="Wrap indicator reads in `if not self.indicator.IsReady: return` or verify readiness before computing trade signals.",
    ),
    "QC-003": RuleDefinition(
        id="QC-003",
        name="Missing IsWarmingUp Guard in OnData",
        severity=Severity.HIGH,
        category=Category.INDICATOR_WARMUP,
        description="Algorithm invokes SetWarmUp() in Initialize() but lacks an early exit `if self.IsWarmingUp: return` in OnData().",
        remediation="Add `if self.IsWarmingUp: return` at the very beginning of `OnData(self, data)` to prevent premature order submissions during warmup.",
    ),
    "QC-004": RuleDefinition(
        id="QC-004",
        name="Unsafe Naked Market Order Execution",
        severity=Severity.MEDIUM,
        category=Category.EXECUTION_SAFETY,
        description="Direct invocation of MarketOrder() with hardcoded share counts without checking portfolio buying power or margin limits.",
        remediation="Prefer `self.SetHoldings(symbol, target_weight)` or leverage the QuantConnect Execution & Risk Management Framework models.",
    ),
    "QC-005": RuleDefinition(
        id="QC-005",
        name="Monolithic Architecture Anti-Pattern",
        severity=Severity.MEDIUM,
        category=Category.ARCHITECTURE,
        description="Strategy mixes Universe, Alpha, Portfolio, Execution, and Risk logic directly into a single monolithic QCAlgorithm class.",
        remediation="Decompose into modular components: `AddAlpha()`, `SetPortfolioConstruction()`, `SetExecution()`, and `SetRiskManagement()`.",
    ),
    "QC-006": RuleDefinition(
        id="QC-006",
        name="Missing Resolution Specification",
        severity=Severity.LOW,
        category=Category.DATA_INTEGRITY,
        description="Adding asset subscription (e.g. AddEquity, AddCrypto) without specifying explicit Resolution (e.g. Resolution.Minute, Resolution.Daily).",
        remediation="Explicitly pass `Resolution.Daily`, `Resolution.Hour`, or `Resolution.Minute` to avoid engine default ambiguities.",
    ),
    "QC-007": RuleDefinition(
        id="QC-007",
        name="Unchecked Slice Data Key Access",
        severity=Severity.HIGH,
        category=Category.DATA_INTEGRITY,
        description="Direct dictionary access on `data[symbol]` or `data[str]` without `data.ContainsKey(symbol)` or null verification.",
        remediation="Guard with `if not data.ContainsKey(symbol) or data[symbol] is None: return` to prevent NullReference exceptions on market holidays or illiquid bars.",
    ),
    "QC-008": RuleDefinition(
        id="QC-008",
        name="Missing Risk Management Model",
        severity=Severity.MEDIUM,
        category=Category.EXECUTION_SAFETY,
        description="Algorithm executes trades without registering a RiskManagementModel (e.g. MaximumDrawdownPercentPortfolio, TrailingStopRiskManagementModel).",
        remediation="Register standard risk controls via `self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))`.",
    ),
    "QC-009": RuleDefinition(
        id="QC-009",
        name="Deprecated QC API Pattern",
        severity=Severity.LOW,
        category=Category.DEPRECATION,
        description="Use of legacy QC v1 constructs or manual datetime string conversions deprecated in modern LEAN.",
        remediation="Use modern Pythonic LEAN date helpers and typed enums (`Resolution`, `Field`, `OrderDirection`).",
    ),
    "QC-010": RuleDefinition(
        id="QC-010",
        name="Hardcoded Trading Thresholds (Overfitting Vulnerability)",
        severity=Severity.MEDIUM,
        category=Category.LOOKAHEAD_BIAS,
        description="Arbitrary magic numbers hardcoded inline in signal generation logic without parameterization or walk-forward validation.",
        remediation="Parameterize variables using `self.GetParameter()` or external optimization configuration.",
    ),
}
