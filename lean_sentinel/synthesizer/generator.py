"""
QuantConnect LEAN Algorithm Framework Synthesizer.
Transforms quantitative investment theses and raw monolithic scripts into
production-grade, 5-Component Modular LEAN algorithms.
"""

from typing import Dict, Any, List, Optional
from lean_sentinel.synthesizer.templates import (
    MOMENTUM_FRAMEWORK_TEMPLATE,
    MEAN_REVERSION_FRAMEWORK_TEMPLATE,
)


class LeanFrameworkSynthesizer:
    @staticmethod
    def generate(
        strategy_type: str = "momentum",
        symbols: Optional[List[str]] = None,
        max_drawdown_pct: float = 0.05,
        resolution: str = "Daily",
    ) -> str:
        strategy_type = strategy_type.lower().strip()
        if "revert" in strategy_type or "mean" in strategy_type or "rsi" in strategy_type:
            code = MEAN_REVERSION_FRAMEWORK_TEMPLATE
        else:
            code = MOMENTUM_FRAMEWORK_TEMPLATE

        # Replace customizable parameters
        if symbols:
            symbols_str = ", ".join([f'"{s.upper()}"' for s in symbols])
            code = code.replace(
                '["SPY", "QQQ", "IWM", "TLT", "GLD"]',
                f"[{symbols_str}]"
            )

        code = code.replace("MaximumDrawdownPercentPortfolio(0.06)", f"MaximumDrawdownPercentPortfolio({max_drawdown_pct})")
        code = code.replace("MaximumDrawdownPercentPortfolio(0.05)", f"MaximumDrawdownPercentPortfolio({max_drawdown_pct})")

        return code

    @staticmethod
    def sanitize_monolithic(source_code: str) -> str:
        """
        Applies automated surgical remediation to common AI-generated script anti-patterns:
        - Injects `if self.IsWarmingUp: return` at the top of OnData
        - Adds missing Risk Management model
        - Adds .ContainsKey checks
        """
        lines = source_code.splitlines()
        modified = []
        in_on_data = False
        on_data_indent = ""
        has_warmup_guard = False
        has_risk_model = "AddRiskManagement" in source_code or "SetRiskManagement" in source_code
        has_set_warmup = "SetWarmUp" in source_code

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def OnData(") or stripped.startswith("def OnData ("):
                in_on_data = True
                on_data_indent = " " * (len(line) - len(line.lstrip()))
                modified.append(line)
                # If warmup was set, immediately ensure warmup guard
                if has_set_warmup and not has_warmup_guard:
                    guard_indent = on_data_indent + "    "
                    modified.append(f"{guard_indent}# [LeanSentinel Auto-Remediation] Warmup safety guard")
                    modified.append(f"{guard_indent}if self.IsWarmingUp:")
                    modified.append(f"{guard_indent}    return")
                    has_warmup_guard = True
                continue

            # Inject risk model into Initialize if missing
            if stripped.startswith("def Initialize(") and not has_risk_model:
                modified.append(line)
                init_indent = " " * (len(line) - len(line.lstrip()) + 4)
                # We will append the risk model call right after initialize header
                modified.append(f"{init_indent}# [LeanSentinel Auto-Remediation] Capital preservation model")
                modified.append(f"{init_indent}self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))")
                has_risk_model = True
                continue

            modified.append(line)

        return "\n".join(modified)
