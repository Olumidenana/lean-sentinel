"""
Python AST Static Analysis Engine for QuantConnect LEAN Algorithms.
Audits code against QuantConnect best practices, anti-patterns, and LLM hallucinations.
"""

import ast
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from lean_sentinel.linter.rules import RULE_CATALOG, Severity, Category


@dataclass
class Finding:
    rule_id: str
    rule_name: str
    severity: Severity
    category: Category
    message: str
    line_number: int
    column: int
    source_snippet: str
    remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "line_number": self.line_number,
            "column": self.column,
            "source_snippet": self.source_snippet,
            "remediation": self.remediation,
        }


@dataclass
class AnalysisResult:
    filename: str
    is_valid_python: bool
    readiness_score: int  # 0 to 100
    grade: str  # A, B, C, D, F
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    findings: List[Finding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "is_valid_python": self.is_valid_python,
            "readiness_score": self.readiness_score,
            "grade": self.grade,
            "total_findings": self.total_findings,
            "severity_breakdown": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "findings": [f.to_dict() for f in self.findings],
            "metadata": self.metadata,
        }


class LeanASTVisitor(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.findings: List[Finding] = []

        # State tracking across AST
        self.has_initialize = False
        self.has_on_data = False
        self.has_set_warmup = False
        self.warmup_line = 0
        self.has_is_warming_up_check = False
        self.indicators_created = set()
        self.indicators_checked_for_ready = set()
        self.indicator_usage_nodes = []
        self.has_framework_components = False
        self.has_risk_model = False
        self.securities_added = []
        self.market_orders = []
        self.raw_data_subscripts = []
        self.magic_numbers = []

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == "Initialize":
            self.has_initialize = True
        elif node.name == "OnData":
            self.has_on_data = True
            # Check if first few statements contain `if self.IsWarmingUp: return`
            for stmt in node.body[:4]:
                if isinstance(stmt, ast.If):
                    if self._check_is_warming_up(stmt.test):
                        self.has_is_warming_up_check = True

        self.generic_visit(node)

    def _check_is_warming_up(self, test_node: ast.AST) -> bool:
        if isinstance(test_node, ast.Attribute):
            if test_node.attr in ("IsWarmingUp", "is_warming_up"):
                return True
        elif isinstance(test_node, ast.UnaryOp) and isinstance(test_node.op, ast.Not):
            return self._check_is_warming_up(test_node.operand)
        return False

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        # Check SetWarmUp
        if func_name == "SetWarmUp":
            self.has_set_warmup = True
            self.warmup_line = node.lineno

        # Check Indicator Creation (EMA, SMA, RSI, MACD, BB, ATR)
        if func_name in ("EMA", "SMA", "RSI", "MACD", "BB", "ATR", "STOCH", "MOM"):
            # Often assigned to self.indicator_name
            pass

        # Check Framework methods
        if func_name in ("AddAlpha", "SetPortfolioConstruction", "SetExecution", "SetRiskManagement", "AddUniverse"):
            self.has_framework_components = True
        if func_name in ("SetRiskManagement", "AddRiskManagement"):
            self.has_risk_model = True

        # Check AddEquity / AddCrypto without explicit Resolution
        if func_name in ("AddEquity", "AddCrypto", "AddForex", "AddFuture", "AddOption"):
            has_resolution = False
            for arg in node.args[1:]:
                if isinstance(arg, ast.Attribute) and (
                    isinstance(arg.value, ast.Name) and arg.value.id == "Resolution"
                ):
                    has_resolution = True
            for kw in node.keywords:
                if kw.arg == "resolution":
                    has_resolution = True

            if not has_resolution and len(node.args) <= 1:
                rule = RULE_CATALOG["QC-006"]
                self.findings.append(
                    Finding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        message=f"`{func_name}()` subscribed without explicit Resolution argument.",
                        line_number=node.lineno,
                        column=node.col_offset,
                        source_snippet=self._get_snippet(node.lineno),
                        remediation=rule.remediation,
                    )
                )

        # Check raw MarketOrder
        if func_name == "MarketOrder":
            rule = RULE_CATALOG["QC-004"]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message="Direct MarketOrder() invocation found. Raw order sizes bypass portfolio weighting constraints.",
                    line_number=node.lineno,
                    column=node.col_offset,
                    source_snippet=self._get_snippet(node.lineno),
                    remediation=rule.remediation,
                )
            )

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        # Look for data[symbol] or data["AAPL"]
        if isinstance(node.value, ast.Name) and node.value.id in ("data", "slice"):
            self.raw_data_subscripts.append(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Look for indicator.Current.Value without IsReady check
        if node.attr == "Value" and isinstance(node.value, ast.Attribute) and node.value.attr == "Current":
            self.indicator_usage_nodes.append(node)

        # Look for Lookahead Bias: accessing future bars or negative history shift
        if node.attr in ("EndTime", "Next", "Tomorrow"):
            rule = RULE_CATALOG["QC-001"]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message=f"Potential lookahead bias detected via direct attribute access `.{node.attr}`.",
                    line_number=node.lineno,
                    column=node.col_offset,
                    source_snippet=self._get_snippet(node.lineno),
                    remediation=rule.remediation,
                )
            )

        self.generic_visit(node)

    def finalize_audit(self):
        # Check warmup mismatch
        if self.has_set_warmup and not self.has_is_warming_up_check and self.has_on_data:
            rule = RULE_CATALOG["QC-003"]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message="SetWarmUp() was declared in Initialize(), but OnData() lacks `if self.IsWarmingUp: return` guard.",
                    line_number=self.warmup_line or 1,
                    column=0,
                    source_snippet=self._get_snippet(self.warmup_line or 1),
                    remediation=rule.remediation,
                )
            )

        # Check indicator usage readiness
        if self.indicator_usage_nodes and "IsReady" not in self.source_code:
            rule = RULE_CATALOG["QC-002"]
            node = self.indicator_usage_nodes[0]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message="Indicators accessed via `.Current.Value` without any `.IsReady` verification in algorithm.",
                    line_number=node.lineno,
                    column=node.col_offset,
                    source_snippet=self._get_snippet(node.lineno),
                    remediation=rule.remediation,
                )
            )

        # Check Unchecked Slice Data Key Access
        if self.raw_data_subscripts and "ContainsKey" not in self.source_code and "contains_key" not in self.source_code:
            rule = RULE_CATALOG["QC-007"]
            node = self.raw_data_subscripts[0]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message="Direct indexing on `data[...]` without any `.ContainsKey()` guards in the algorithm.",
                    line_number=node.lineno,
                    column=node.col_offset,
                    source_snippet=self._get_snippet(node.lineno),
                    remediation=rule.remediation,
                )
            )

        # Check Monolithic Architecture vs Framework
        if not self.has_framework_components and len(self.lines) > 80:
            rule = RULE_CATALOG["QC-005"]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message="Algorithm is monolithic (>80 lines) without modular LEAN framework models (Alpha, Portfolio, Risk).",
                    line_number=1,
                    column=0,
                    source_snippet=self._get_snippet(1),
                    remediation=rule.remediation,
                )
            )

        # Check Missing Risk Management
        if not self.has_risk_model:
            rule = RULE_CATALOG["QC-008"]
            self.findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    message="No explicit Risk Management model registered (e.g. MaximumDrawdownPercentPortfolio).",
                    line_number=1,
                    column=0,
                    source_snippet=self._get_snippet(1),
                    remediation=rule.remediation,
                )
            )


class LeanASTAnalyzer:
    """
    Main entry point for analyzing QuantConnect LEAN Python algorithms.
    """

    def analyze_source(self, source_code: str, filename: str = "algorithm.py") -> AnalysisResult:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return AnalysisResult(
                filename=filename,
                is_valid_python=False,
                readiness_score=0,
                grade="F",
                total_findings=1,
                critical_count=1,
                high_count=0,
                medium_count=0,
                low_count=0,
                info_count=0,
                findings=[
                    Finding(
                        rule_id="SYNTAX-001",
                        rule_name="Python Syntax Error",
                        severity=Severity.CRITICAL,
                        category=Category.DATA_INTEGRITY,
                        message=f"Syntax Error: {e.msg}",
                        line_number=e.lineno or 1,
                        column=e.offset or 0,
                        source_snippet=e.text.strip() if e.text else "",
                        remediation="Correct standard Python syntax before running LEAN compilation.",
                    )
                ],
                metadata={"lines": len(source_code.splitlines())},
            )

        visitor = LeanASTVisitor(source_code)
        visitor.visit(tree)
        visitor.finalize_audit()

        # Score calculation
        deductions = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1,
        }

        penalty = 0
        crit_count = high_count = med_count = low_count = info_count = 0

        for f in visitor.findings:
            penalty += deductions.get(f.severity, 5)
            if f.severity == Severity.CRITICAL:
                crit_count += 1
            elif f.severity == Severity.HIGH:
                high_count += 1
            elif f.severity == Severity.MEDIUM:
                med_count += 1
            elif f.severity == Severity.LOW:
                low_count += 1
            else:
                info_count += 1

        readiness_score = max(0, 100 - penalty)

        if readiness_score >= 90:
            grade = "A"
        elif readiness_score >= 80:
            grade = "B"
        elif readiness_score >= 70:
            grade = "C"
        elif readiness_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return AnalysisResult(
            filename=filename,
            is_valid_python=True,
            readiness_score=readiness_score,
            grade=grade,
            total_findings=len(visitor.findings),
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            info_count=info_count,
            findings=visitor.findings,
            metadata={
                "lines_of_code": len(visitor.lines),
                "has_initialize": visitor.has_initialize,
                "has_on_data": visitor.has_on_data,
                "has_framework": visitor.has_framework_components,
            },
        )
