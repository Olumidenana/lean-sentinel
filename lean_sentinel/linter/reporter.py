"""
Reporting utilities for LeanSentinel static analysis results.
Supports CLI text formatting, Markdown generation, and JSON exports.
"""

import json
from typing import Dict, Any
from lean_sentinel.linter.analyzer import AnalysisResult


class LeanReporter:
    @staticmethod
    def to_cli_text(result: AnalysisResult) -> str:
        lines = []
        lines.append("=" * 72)
        lines.append(f"  LEANSENTINEL AUDIT REPORT: {result.filename}")
        lines.append(f"  Readiness Score: {result.readiness_score}/100  [Grade: {result.grade}]")
        lines.append(
            f"  Findings: {result.total_findings} "
            f"(Critical: {result.critical_count}, High: {result.high_count}, "
            f"Med: {result.medium_count}, Low: {result.low_count})"
        )
        lines.append("=" * 72)

        if not result.findings:
            lines.append("  [PASS] All QuantConnect LEAN architecture checks PASSED! Zero defects found.")
            lines.append("=" * 72)
            return "\n".join(lines)

        lines.append("")
        for idx, f in enumerate(result.findings, 1):
            lines.append(f"[{idx}] {f.severity.value} - {f.rule_id}: {f.rule_name}")
            lines.append(f"    Line {f.line_number}:{f.column} -> {f.message}")
            if f.source_snippet:
                lines.append(f"    Snippet:    `{f.source_snippet}`")
            lines.append(f"    Remedy:     {f.remediation}")
            lines.append("-" * 72)

        return "\n".join(lines)

    @staticmethod
    def to_markdown(result: AnalysisResult) -> str:
        md = []
        md.append(f"# 🛡️ LeanSentinel Audit Report: `{result.filename}`\n")
        md.append(f"**QuantConnect LEAN Readiness Score:** `{result.readiness_score} / 100` (Grade: **{result.grade}**)\n")
        md.append("| Metric | Count |")
        md.append("| :--- | :--- |")
        md.append(f"| **Total Violations** | {result.total_findings} |")
        md.append(f"| 🚨 Critical | {result.critical_count} |")
        md.append(f"| ⚠️ High | {result.high_count} |")
        md.append(f"| 🔶 Medium | {result.medium_count} |")
        md.append(f"| ℹ️ Low | {result.low_count} |\n")

        if not result.findings:
            md.append("### ✅ Clean Bill of Health\nNo architectural anti-patterns, lookahead leaks, or un-warmed indicators detected.\n")
            return "\n".join(md)

        md.append("## Identified Deficiencies & Recommendations\n")
        for f in result.findings:
            md.append(f"### `{f.rule_id}`: {f.rule_name} `[{f.severity.value}]`")
            md.append(f"- **Location:** Line {f.line_number}, Column {f.column}")
            md.append(f"- **Category:** {f.category.value}")
            md.append(f"- **Issue:** {f.message}")
            if f.source_snippet:
                md.append(f"- **Code:** `{f.source_snippet}`")
            md.append(f"- **Required Fix:** {f.remediation}\n")

        return "\n".join(md)

    @staticmethod
    def to_json(result: AnalysisResult, indent: int = 2) -> str:
        return json.dumps(result.to_dict(), indent=indent)
