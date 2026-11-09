# 🛡️ LeanSentinel

> **Autonomous AI Agent Supervisor & Anti-Hallucination Guardrails for QuantConnect LEAN**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FOlumidenana%2Flean-sentinel)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![QuantConnect LEAN](https://img.shields.io/badge/QuantConnect-LEAN%20Engine-amber.svg)](https://www.quantconnect.com)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Remote%20Ready-green.svg)](https://github.com/QuantConnect/mcp-server)

LeanSentinel is an institutional-grade static analysis engine, strategy synthesizer, and overfitting diagnostic supervisor designed specifically for **QuantConnect LEAN** algorithmic trading systems and AI agentic workflows (**Mia V2, Claude Code, Cursor, Copilot, Devin**).

---

## ⚡ The Problem: The AI-to-LEAN Impedance Mismatch

With QuantConnect's release of the **Remote Model Context Protocol (MCP) Server**, autonomous AI agents can design, code, and backtest trading strategies directly against cloud clusters. 

However, generalist LLMs frequently hallucinate invalid LEAN idioms, introduce subtle lookahead bias, execute trades on un-warmed indicators, and generate monolithic spaghetti code that violates QuantConnect's canonical 5-component modular architecture. Furthermore, when agents run 50+ backtests in a session, traditional Sharpe ratios become statistical illusions due to backtest overfitting.

**LeanSentinel acts as the intelligent pre-flight gatekeeper**:

```
 ┌─────────────────────────────────────────────────────────────┐
 │                      AI Coding Agent                        │
 │           (Mia V2 / Claude Code / Cursor / Devin)           │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                  🛡️  LeanSentinel Engine                    │
 │                                                             │
 │  1. AST Anti-Hallucination Linter (10 QC Rule Checks)       │
 │  2. 5-Component Modular Synthesizer (Universe/Alpha/Risk)   │
 │  3. Deflated Sharpe Ratio (DSR) & Overfitting Verifier      │
 │  4. Automated Surgical Code Remediation                     │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                         [Clean / Validated]
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                QuantConnect Cloud Platform                  │
 │          (Remote MCP: api/v2/mcp  |  LEAN Engine)           │
 └─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

- **AST-Based Linter (`QC-001` to `QC-010`)**: Instant static analysis in milliseconds without Docker overhead or cloud billing.
- **Deflated Sharpe Ratio (DSR)**: Implements Marcos Lopez de Prado's statistical formula to penalize multiple testing and calculate genuine statistical significance ($p > 0.95$).
- **5-Component Framework Synthesizer**: Converts monolithic single-script algorithms into modular QuantConnect Framework components:
  1. *Universe Selection Model*
  2. *Alpha Creation Model*
  3. *Portfolio Construction Model*
  4. *Execution Model*
  5. *Risk Management Model*
- **Surgical Auto-Remediation**: Injects `self.IsWarmingUp` guards, defensive dictionary keys (`ContainsKey`), and circuit breakers automatically.
- **Interactive Web Studio**: Sleek QuantConnect dark-mode UI with live vulnerability radars, CodeMirror editing, Monte Carlo simulation, and equity curve visualizations.
- **Remote MCP Bridge**: Connects directly to `https://www.quantconnect.com/api/v2/mcp` or runs in offline simulation mode.

---

## 📦 Quickstart

### 1. Installation
Clone the repository:
```bash
git clone https://github.com/Olumidenana/lean-sentinel.git
cd lean-sentinel
pip install -r requirements.txt
```

### 2. Run the Interactive Showcase
```bash
python demo.py
```

### 3. Launch the Web Studio
```bash
python -m lean_sentinel.cli serve --port 8000
```
Then open `http://localhost:8000` in your browser.

---

## 🛠️ CLI Usage Guide

### Audit an Algorithm for Vulnerabilities
```bash
# Terminal output table
python -m lean_sentinel.cli audit examples/vulnerable_algorithm.py

# Export as GitHub Markdown
python -m lean_sentinel.cli audit examples/vulnerable_algorithm.py --format markdown

# Export as JSON for CI/CD
python -m lean_sentinel.cli audit examples/vulnerable_algorithm.py --format json
```

### Automatically Fix Code Anti-Patterns
```bash
python -m lean_sentinel.cli fix examples/vulnerable_algorithm.py --output cleaned_algo.py
```

### Synthesize a Production 5-Component Algorithm
```bash
python -m lean_sentinel.cli synthesize --type momentum --symbols "SPY,QQQ,IWM" --output institutional_momentum.py
```

### Evaluate Overfitting via Deflated Sharpe Ratio
```bash
python -m lean_sentinel.cli dsr --sharpe 2.15 --trials 50
```

---

## 📋 Rule Catalog

| Rule ID | Name | Severity | Description |
| :--- | :--- | :--- | :--- |
| **`QC-001`** | **Lookahead Bias / Future Leakage** | `CRITICAL` | Accessing unshifted future bars or negative history offsets in `OnData()`. |
| **`QC-002`** | **Unchecked Indicator Readiness** | `HIGH` | Reading `.Current.Value` without first verifying `indicator.IsReady`. |
| **`QC-003`** | **Missing Warmup Guard** | `HIGH` | Invoking `SetWarmUp()` in `Initialize()` without early exit `if self.IsWarmingUp: return` in `OnData()`. |
| **`QC-004`** | **Unsafe MarketOrder Sizing** | `MEDIUM` | Hardcoded share counts in raw `MarketOrder()` bypassing portfolio margin. |
| **`QC-005`** | **Monolithic Architecture Smell** | `MEDIUM` | Exceeding 80 lines without decomposing into the 5-component QC Algorithm Framework. |
| **`QC-006`** | **Missing Resolution Argument** | `LOW` | Subscribing to assets (`AddEquity`, `AddCrypto`) without explicit `Resolution`. |
| **`QC-007`** | **Unchecked Slice Access** | `HIGH` | Direct indexing `data[symbol]` without `data.ContainsKey(symbol)` guard. |
| **`QC-008`** | **Missing Risk Model** | `MEDIUM` | Executing orders without a registered `RiskManagementModel` (e.g. `MaximumDrawdownPercentPortfolio`). |
| **`QC-009`** | **Deprecated QC API Usage** | `LOW` | Legacy QC v1 constructs or manual datetime string conversions. |
| **`QC-010`** | **Hardcoded Magic Numbers** | `MEDIUM` | Inline signal thresholds creating severe curve-fitting risks. |

---

## 📊 Deflated Sharpe Ratio (DSR) Formulation

Given an observed annualized Sharpe ratio $SR$, number of independent backtest trials $N$, variance of trials $\sigma^2_{SR}$, skewness $\gamma_3$, and kurtosis $\gamma_4$:

$$DSR = \Phi \left( \frac{(SR - SR_0) \sqrt{T-1}}{\sqrt{1 - \gamma_3 SR + \frac{\gamma_4 - 1}{4} SR^2}} \right)$$

where the expected maximum Sharpe ratio under the null hypothesis is:

$$SR_0 \approx \sqrt{2 \ln N} \left( 1 - \frac{\gamma}{\sqrt{2 \ln N}} \right)$$

LeanSentinel computes both the exact DSR probability and the adjusted **Haircut Sharpe Ratio** to prevent false discoveries.

---

## 📄 Proposal & Integration Roadmap

For details on how LeanSentinel can be directly integrated into QuantConnect's **Remote MCP Server**, **LEAN CLI**, or **Mia V2 Web IDE**, see [EXECUTIVE_PROPOSAL.md](file:///C:/Users/giant/.gemini/antigravity/scratch/lean-sentinel/EXECUTIVE_PROPOSAL.md).

---

## ⚖️ License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
