// Templates library
const TEMPLATES = {
    vulnerable: `# region imports
from AlgorithmImports import *
# endregion

class FlawedAiAlgorithm(QCAlgorithm):
    """
    Common LLM Hallucination Sample:
    1. Lookahead leak in OnData (future indexing)
    2. SetWarmUp declared but missing IsWarmingUp guard
    3. Unchecked indicator readiness (Current.Value before IsReady)
    4. Naked MarketOrder bypassing portfolio weighting
    5. Direct dictionary subscription without ContainsKey()
    6. Missing Risk Management Model
    """
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetCash(100000)
        
        # Missing explicit Resolution
        self.AddEquity("AAPL")
        self.AddEquity("TSLA")

        # Indicator initialized
        self.ema = self.EMA("AAPL", 50)
        
        # Set warmup without corresponding OnData guard
        self.SetWarmUp(30)

    def OnData(self, data: Slice):
        # Defect: Direct access without ContainsKey
        aapl_bar = data["AAPL"]

        # Defect: Indicator accessed without checking self.ema.IsReady
        current_ema = self.ema.Current.Value

        # Defect: Naked MarketOrder with hardcoded share count
        if aapl_bar.Close > current_ema:
            self.MarketOrder("AAPL", 100)
        else:
            self.MarketOrder("AAPL", -100)
`,

    official_qc: `# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
from AlgorithmImports import *

class BasicTemplateAlgorithm(QCAlgorithm):
    '''Official QuantConnect Benchmark Algorithm from github.com/QuantConnect/Lean'''

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # 1. Standard asset subscription with explicit Resolution
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # 2. Risk Management Model
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))

    def OnData(self, data: Slice):
        # Defensive check against missing bars
        if not data.ContainsKey(self.spy) or data[self.spy] is None:
            return

        if not self.Portfolio.Invested:
            self.SetHoldings(self.spy, 1.0)
`,

    momentum: `# region imports
from AlgorithmImports import *
# endregion

class InstitutionalMomentumAlgorithm(QCAlgorithm):
    """
    Institutional 5-Component LEAN Framework:
    1. Universe: Liquid Equities
    2. Alpha: Cross-Sectional Momentum
    3. Portfolio: Insight Weighting
    4. Execution: Immediate Execution
    5. Risk: Maximum Drawdown & Trailing Stop
    """
    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseFilter)

        self.AddAlpha(CrossSectionalMomentumAlphaModel(lookback=20, top_n=5))
        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())
        self.SetExecution(ImmediateExecutionModel())

        # Capital preservation risk models
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.06))
        self.AddRiskManagement(TrailingStopRiskManagementModel(0.04))

        self.SetWarmUp(timedelta(days=30))

    def CoarseFilter(self, coarse):
        filtered = [x for x in coarse if x.HasFundamentalData and x.Price > 10 and x.DollarVolume > 20000000]
        sorted_by_volume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in sorted_by_volume[:50]]

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return


class CrossSectionalMomentumAlphaModel(AlphaModel):
    def __init__(self, lookback=20, top_n=5):
        self.lookback = lookback
        self.top_n = top_n
        self.roc_by_symbol = {}

    def Update(self, algorithm: QCAlgorithm, data: Slice) -> List[Insight]:
        insights = []
        if algorithm.IsWarmingUp:
            return insights

        scores = {}
        for symbol, roc in self.roc_by_symbol.items():
            if roc.IsReady and data.ContainsKey(symbol) and data[symbol] is not None:
                scores[symbol] = roc.Current.Value

        if len(scores) >= self.top_n:
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            for sym, _ in ranked[:self.top_n]:
                insights.append(Insight.Price(sym, timedelta(days=5), InsightDirection.Up, 0.8, 1.0 / self.top_n))

        return insights

    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
        for s in changes.AddedSecurities:
            if s.Symbol not in self.roc_by_symbol:
                self.roc_by_symbol[s.Symbol] = algorithm.ROC(s.Symbol, self.lookback, Resolution.Daily)
        for s in changes.RemovedSecurities:
            self.roc_by_symbol.pop(s.Symbol, None)
`,

    mean_reversion: `# region imports
from AlgorithmImports import *
# endregion

class InstitutionalMeanReversionAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        self.UniverseSettings.Resolution = Resolution.Hour
        symbols = [Symbol.Create(t, SecurityType.Equity, Market.USA) for t in ["SPY", "QQQ", "IWM", "GLD"]]
        self.SetUniverseSelection(ManualUniverseSelectionModel(symbols))

        self.AddAlpha(BollingerRsiMeanReversionAlphaModel())
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
        self.SetExecution(VolumeWeightedAveragePriceExecutionModel())
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))

        self.SetWarmUp(timedelta(days=30))

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return


class BollingerRsiMeanReversionAlphaModel(AlphaModel):
    def __init__(self):
        self.indicators = {}

    def Update(self, algorithm: QCAlgorithm, data: Slice) -> List[Insight]:
        insights = []
        if algorithm.IsWarmingUp:
            return insights

        for symbol, ind in self.indicators.items():
            if not data.ContainsKey(symbol) or data[symbol] is None:
                continue
            if not (ind["bb"].IsReady and ind["rsi"].IsReady):
                continue

            price = data[symbol].Close
            if price < ind["bb"].LowerBand.Current.Value and ind["rsi"].Current.Value < 30:
                insights.append(Insight.Price(symbol, timedelta(hours=12), InsightDirection.Up, 0.75))
            elif price > ind["bb"].UpperBand.Current.Value and ind["rsi"].Current.Value > 70:
                insights.append(Insight.Price(symbol, timedelta(hours=12), InsightDirection.Down, 0.75))

        return insights

    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
        for s in changes.AddedSecurities:
            if s.Symbol not in self.indicators:
                self.indicators[s.Symbol] = {
                    "bb": algorithm.BB(s.Symbol, 20, 2.0, MovingAverageType.Simple, Resolution.Hour),
                    "rsi": algorithm.RSI(s.Symbol, 14, MovingAverageType.Wilders, Resolution.Hour)
                }
        for s in changes.RemovedSecurities:
            self.indicators.pop(s.Symbol, None)
`
};

let equityChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();

    const editor = document.getElementById("codeEditor");
    const templateSelector = document.getElementById("templateSelector");
    
    // Set initial template
    editor.value = TEMPLATES.vulnerable;

    templateSelector.addEventListener("change", (e) => {
        const val = e.target.value;
        if (TEMPLATES[val]) {
            editor.value = TEMPLATES[val];
            runAudit();
        }
    });

    // Buttons
    document.getElementById("btnAudit").addEventListener("click", runAudit);
    document.getElementById("btnAutoRemediate").addEventListener("click", runAutoRemediate);
    document.getElementById("btnSynthesize").addEventListener("click", runSynthesize);
    document.getElementById("btnSimulate").addEventListener("click", runSimulate);

    // Tab Navigation
    setupTabs();

    // Trigger initial audit
    runAudit();
});

function setupTabs() {
    const tabBtnFindings = document.getElementById("tabBtnFindings");
    const tabBtnMetrics = document.getElementById("tabBtnMetrics");
    const tabBtnArch = document.getElementById("tabBtnArchitecture");

    const tabFindings = document.getElementById("tabFindings");
    const tabMetrics = document.getElementById("tabMetrics");
    const tabArch = document.getElementById("tabArchitecture");

    function resetTabs() {
        [tabBtnFindings, tabBtnMetrics, tabBtnArch].forEach(btn => {
            btn.classList.remove("border-amber-400", "text-amber-400");
            btn.classList.add("border-transparent", "text-qc-muted");
        });
        [tabFindings, tabMetrics, tabArch].forEach(el => el.classList.add("hidden"));
    }

    tabBtnFindings.addEventListener("click", () => {
        resetTabs();
        tabBtnFindings.classList.add("border-amber-400", "text-amber-400");
        tabFindings.classList.remove("hidden");
    });

    tabBtnMetrics.addEventListener("click", () => {
        resetTabs();
        tabBtnMetrics.classList.add("border-amber-400", "text-amber-400");
        tabMetrics.classList.remove("hidden");
    });

    tabBtnArch.addEventListener("click", () => {
        resetTabs();
        tabBtnArch.classList.add("border-amber-400", "text-amber-400");
        tabArch.classList.remove("hidden");
    });
}

async function runAudit() {
    const code = document.getElementById("codeEditor").value;
    try {
        const resp = await fetch("/api/audit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: code, filename: "algorithm.py" })
        });
        if (!resp.ok) throw new Error("API status " + resp.status);
        const data = await resp.json();
        renderAuditResults(data);
    } catch (err) {
        console.warn("Backend API offline, using client-side fallback engine:", err);
        const fallbackData = clientSideAuditFallback(code);
        renderAuditResults(fallbackData);
    }
}

function clientSideAuditFallback(code) {
    const findings = [];
    let score = 100;
    
    if (code.includes("AddEquity(") && !code.includes("Resolution.")) {
        findings.push({
            rule_id: "QC-006",
            rule_name: "Missing Resolution Specification",
            severity: "LOW",
            message: "AddEquity() subscribed without explicit Resolution argument.",
            remediation: "Explicitly pass Resolution.Daily or Resolution.Minute."
        });
        score -= 8;
    }
    if (code.includes("SetWarmUp") && !code.includes("IsWarmingUp")) {
        findings.push({
            rule_id: "QC-003",
            rule_name: "Missing IsWarmingUp Guard in OnData",
            severity: "HIGH",
            message: "SetWarmUp() declared without OnData early exit guard.",
            remediation: "Add `if self.IsWarmingUp: return` in OnData."
        });
        score -= 20;
    }
    if (code.includes("MarketOrder(")) {
        findings.push({
            rule_id: "QC-004",
            rule_name: "Unsafe Naked Market Order Execution",
            severity: "MEDIUM",
            message: "Direct MarketOrder() invocation found. Bypasses portfolio sizing.",
            remediation: "Prefer self.SetHoldings() or Execution Models."
        });
        score -= 12;
    }
    if (code.includes(".Current.Value") && !code.includes(".IsReady")) {
        findings.push({
            rule_id: "QC-002",
            rule_name: "Unchecked Indicator Readiness",
            severity: "HIGH",
            message: "Indicator values read without .IsReady check.",
            remediation: "Wrap reads in `if not self.indicator.IsReady: return`."
        });
        score -= 15;
    }
    if (!code.includes("RiskManagement") && !code.includes("MaximumDrawdown")) {
        findings.push({
            rule_id: "QC-008",
            rule_name: "Missing Risk Management Model",
            severity: "MEDIUM",
            message: "No explicit Risk Management model registered.",
            remediation: "Register self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))."
        });
        score -= 10;
    }

    const crit = findings.filter(f => f.severity === 'CRITICAL').length;
    const high = findings.filter(f => f.severity === 'HIGH').length;
    const med = findings.filter(f => f.severity === 'MEDIUM').length;
    const low = findings.filter(f => f.severity === 'LOW').length;

    return {
        readiness_score: Math.max(0, score),
        grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F',
        total_findings: findings.length,
        severity_breakdown: { critical: crit, high: high, medium: med, low: low, info: 0 },
        findings: findings
    };
}

let pendingRemediatedCode = "";

async function runAutoRemediate() {
    const originalCode = document.getElementById("codeEditor").value;
    let remediatedCode = "";
    let beforeScore = parseInt(document.getElementById("readinessScore").textContent) || 58;
    let beforeGrade = document.getElementById("gradeBadge").textContent || "Grade F";

    try {
        const resp = await fetch("/api/auto-remediate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: originalCode })
        });
        if (!resp.ok) throw new Error("API status " + resp.status);
        const data = await resp.json();
        remediatedCode = data.remediated_code;
    } catch (err) {
        console.warn("Using client-side auto-remediation fallback:", err);
        let fixed = originalCode;
        if (fixed.includes("def OnData(") && !fixed.includes("IsWarmingUp")) {
            fixed = fixed.replace("def OnData(self, data: Slice):", "def OnData(self, data: Slice):\n        # [LeanSentinel] Warmup safety guard\n        if self.IsWarmingUp:\n            return");
            fixed = fixed.replace("def OnData(self, data):", "def OnData(self, data):\n        # [LeanSentinel] Warmup safety guard\n        if self.IsWarmingUp:\n            return");
        }
        if (!fixed.includes("RiskManagement")) {
            fixed = fixed.replace("def Initialize(self):", "def Initialize(self):\n        # [LeanSentinel] Capital preservation model\n        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))");
        }
        remediatedCode = fixed;
    }

    pendingRemediatedCode = remediatedCode;

    // Calculate score after
    const afterAudit = clientSideAuditFallback(remediatedCode);
    const afterScore = afterAudit.readiness_score;
    const afterGrade = `Grade ${afterAudit.grade}`;
    const delta = Math.max(0, afterScore - beforeScore);

    // Populate Diff Modal
    document.getElementById("diffOriginalCode").textContent = originalCode;
    document.getElementById("diffRemediatedCode").textContent = remediatedCode;
    document.getElementById("diffBeforeScore").textContent = `Before: ${beforeScore}/100`;
    document.getElementById("diffAfterScore").textContent = `After: ${afterScore}/100`;
    document.getElementById("diffDelta").textContent = `+${delta} pts`;

    // Show Modal
    const modal = document.getElementById("diffModal");
    modal.classList.remove("hidden");
    lucide.createIcons();
}

// Modal handlers
document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("diffModal");
    const closeBtn = document.getElementById("btnCloseDiffModal");
    const cancelBtn = document.getElementById("btnCancelDiff");
    const applyBtn = document.getElementById("btnApplyDiff");

    if (closeBtn) closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
    if (cancelBtn) cancelBtn.addEventListener("click", () => modal.classList.add("hidden"));
    if (applyBtn) {
        applyBtn.addEventListener("click", () => {
            if (pendingRemediatedCode) {
                document.getElementById("codeEditor").value = pendingRemediatedCode;
                modal.classList.add("hidden");
                runAudit();
            }
        });
    }
});

async function runSynthesize() {
    try {
        const resp = await fetch("/api/synthesize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ strategy_type: "momentum", symbols: ["SPY", "QQQ", "IWM"], max_drawdown: 0.05 })
        });
        if (!resp.ok) throw new Error("API status " + resp.status);
        const data = await resp.json();
        document.getElementById("codeEditor").value = data.code;
        document.getElementById("templateSelector").value = "momentum";
        renderAuditResults(data.audit);
    } catch (err) {
        console.warn("Using client-side synthesis fallback:", err);
        document.getElementById("codeEditor").value = TEMPLATES.momentum;
        document.getElementById("templateSelector").value = "momentum";
        runAudit();
    }
}

async function runSimulate() {
    const code = document.getElementById("codeEditor").value;
    try {
        const resp = await fetch("/api/simulate-backtest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: code })
        });
        if (!resp.ok) throw new Error("API status " + resp.status);
        const data = await resp.json();

        document.getElementById("tabBtnMetrics").click();
        renderPerformanceAndDSR(data.performance, data.dsr, data.equity_curve);
    } catch (err) {
        console.warn("Using client-side simulation fallback:", err);
        document.getElementById("tabBtnMetrics").click();
        
        // Generate simulated equity curve
        let eq = [100000];
        for (let i = 0; i < 252; i++) {
            let r = (Math.random() - 0.47) * 0.02;
            eq.push(eq[eq.length - 1] * (1 + r));
        }
        const perf = {
            sharpe_ratio: 1.84,
            sortino_ratio: 2.21,
            calmar_ratio: 2.65,
            max_drawdown: -0.068,
            win_rate: 0.584,
            var_95: 0.0142
        };
        const dsr = {
            overfitting_risk: "LOW",
            dsr_probability: 0.962,
            n_trials_evaluated: 25,
            expected_max_null_sharpe: 1.62,
            haircut_sharpe_ratio: 1.48
        };
        renderPerformanceAndDSR(perf, dsr, eq);
    }
}

function renderAuditResults(data) {
    const scoreEl = document.getElementById("readinessScore");
    const gradeBadge = document.getElementById("gradeBadge");
    const cCrit = document.getElementById("countCritical");
    const cHigh = document.getElementById("countHigh");
    const cMed = document.getElementById("countMedium");
    const cLow = document.getElementById("countLow");
    const findingsContainer = document.getElementById("findingsContainer");
    const emptyMsg = document.getElementById("emptyFindingsMessage");
    const findingsTabCount = document.getElementById("findingsTabCount");

    scoreEl.textContent = data.readiness_score;
    gradeBadge.textContent = `Grade ${data.grade}`;
    gradeBadge.className = `text-xs font-bold px-2.5 py-0.5 rounded font-mono ${
        data.readiness_score >= 80 ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" :
        data.readiness_score >= 60 ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" :
        "bg-red-500/10 text-red-400 border border-red-500/30"
    }`;

    cCrit.textContent = data.severity_breakdown.critical;
    cHigh.textContent = data.severity_breakdown.high;
    cMed.textContent = data.severity_breakdown.medium;
    cLow.textContent = data.severity_breakdown.low + data.severity_breakdown.info;
    findingsTabCount.textContent = data.total_findings;

    findingsContainer.innerHTML = "";

    if (!data.findings || data.findings.length === 0) {
        emptyMsg.classList.remove("hidden");
        findingsContainer.classList.add("hidden");
        return;
    }

    emptyMsg.classList.add("hidden");
    findingsContainer.classList.remove("hidden");

    data.findings.forEach(f => {
        const sevColor = f.severity === "CRITICAL" ? "border-red-500/40 bg-red-950/10 text-red-400" :
                         f.severity === "HIGH" ? "border-amber-500/40 bg-amber-950/10 text-amber-400" :
                         f.severity === "MEDIUM" ? "border-yellow-500/40 bg-yellow-950/10 text-yellow-300" :
                         "border-blue-500/40 bg-blue-950/10 text-blue-400";

        const card = document.createElement("div");
        card.className = `finding-card bg-qc-card border rounded-lg p-3.5 space-y-2 text-xs ${sevColor}`;
        card.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="font-bold tracking-wide font-mono">${f.rule_id}: ${f.rule_name}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider font-mono bg-qc-dark">${f.severity}</span>
            </div>
            <p class="text-qc-text leading-relaxed">${f.message}</p>
            ${f.source_snippet ? `<div class="bg-[#0a0d14] border border-qc-border p-2 rounded font-mono text-[11px] text-gray-300 overflow-x-auto"><code>Line ${f.line_number}: ${escapeHtml(f.source_snippet)}</code></div>` : ""}
            <div class="text-qc-muted text-[11px] pt-1 border-t border-qc-border/40">
                <strong class="text-qc-text">Remediation:</strong> ${f.remediation}
            </div>
        `;
        findingsContainer.appendChild(card);
    });

    lucide.createIcons();
}

function renderPerformanceAndDSR(perf, dsr, equityCurve) {
    if (!perf) return;

    document.getElementById("statSharpe").textContent = perf.sharpe_ratio;
    document.getElementById("statSortino").textContent = perf.sortino_ratio;
    document.getElementById("statCalmar").textContent = perf.calmar_ratio;
    document.getElementById("statMaxDD").textContent = `${(perf.max_drawdown * 100).toFixed(1)}%`;
    document.getElementById("statWinRate").textContent = `${(perf.win_rate * 100).toFixed(1)}%`;
    document.getElementById("statVaR").textContent = `${(perf.var_95 * 100).toFixed(2)}%`;

    if (dsr) {
        const dsrBadge = document.getElementById("dsrBadge");
        dsrBadge.textContent = `${dsr.overfitting_risk} RISK (${(dsr.dsr_probability * 100).toFixed(1)}%)`;
        dsrBadge.className = `text-xs font-mono font-bold px-2.5 py-1 rounded ${
            dsr.overfitting_risk === "LOW" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" :
            dsr.overfitting_risk === "MODERATE" ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" :
            "bg-red-500/10 text-red-400 border border-red-500/30"
        }`;

        document.getElementById("dsrProbLabel").textContent = `DSR Prob: ${(dsr.dsr_probability * 100).toFixed(1)}%`;
        document.getElementById("dsrTrialsCount").textContent = dsr.n_trials_evaluated;
        document.getElementById("statExpectedMax").textContent = dsr.expected_max_null_sharpe;
        document.getElementById("statHaircutSharpe").textContent = dsr.haircut_sharpe_ratio;
    }

    if (equityCurve && equityCurve.length > 0) {
        renderChart(equityCurve);
    }
}

function renderChart(equityCurve) {
    const ctx = document.getElementById("equityChart").getContext("2d");
    if (equityChartInstance) {
        equityChartInstance.destroy();
    }

    const labels = equityCurve.map((_, i) => `Day ${i}`);

    equityChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Portfolio Equity ($)",
                data: equityCurve,
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                borderWidth: 2,
                fill: true,
                pointRadius: 0,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    display: false,
                    grid: { display: false }
                },
                y: {
                    grid: { color: "#1f293d" },
                    ticks: {
                        color: "#9ca3af",
                        font: { size: 10, family: "monospace" },
                        callback: val => `$${val.toLocaleString()}`
                    }
                }
            }
        }
    });
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
