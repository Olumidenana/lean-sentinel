"""
FastAPI Server for LeanSentinel Interactive Studio.
Provides REST endpoints for static analysis, strategy synthesis, DSR calculation, and backtest simulation.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from lean_sentinel.linter.analyzer import LeanASTAnalyzer
from lean_sentinel.statistics.metrics import PerformanceMetrics
from lean_sentinel.statistics.dsr import calculate_dsr, haircut_sharpe_ratio
from lean_sentinel.statistics.sensitivity import SensitivityEngine
from lean_sentinel.synthesizer.generator import LeanFrameworkSynthesizer
from lean_sentinel.mcp_bridge.mock_server import MockQuantConnectMCPServer
import numpy as np

app = FastAPI(
    title="LeanSentinel Studio",
    description="Institutional AI Guardrails & Strategy Supervisor for QuantConnect LEAN",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
analyzer = LeanASTAnalyzer()
mock_server = MockQuantConnectMCPServer()


class AuditRequest(BaseModel):
    code: str
    filename: Optional[str] = "algorithm.py"


class SynthesizeRequest(BaseModel):
    strategy_type: str = "momentum"
    symbols: Optional[List[str]] = Field(default_factory=lambda: ["SPY", "QQQ", "IWM"])
    max_drawdown: float = 0.05


class RemediationRequest(BaseModel):
    code: str


class DSRRequest(BaseModel):
    observed_sharpe: float = 1.85
    n_trials: int = 25
    returns: Optional[List[float]] = None


@app.post("/api/audit")
def audit_code(req: AuditRequest) -> Dict[str, Any]:
    res = analyzer.analyze_source(req.code, filename=req.filename or "algorithm.py")
    return res.to_dict()


@app.post("/api/synthesize")
def synthesize_framework(req: SynthesizeRequest) -> Dict[str, Any]:
    generated_code = LeanFrameworkSynthesizer.generate(
        strategy_type=req.strategy_type,
        symbols=req.symbols,
        max_drawdown_pct=req.max_drawdown,
    )
    audit_res = analyzer.analyze_source(generated_code, filename="synthesized_framework.py")
    return {
        "code": generated_code,
        "audit": audit_res.to_dict(),
    }


@app.post("/api/auto-remediate")
def auto_remediate(req: RemediationRequest) -> Dict[str, Any]:
    fixed_code = LeanFrameworkSynthesizer.sanitize_monolithic(req.code)
    audit_res = analyzer.analyze_source(fixed_code, filename="remediated_algorithm.py")
    return {
        "remediated_code": fixed_code,
        "audit": audit_res.to_dict(),
    }


@app.post("/api/calculate-dsr")
def compute_dsr_endpoint(req: DSRRequest) -> Dict[str, Any]:
    # If returns not provided, generate a realistic empirical distribution
    returns = req.returns
    if not returns or len(returns) < 10:
        np.random.seed(101)
        returns = list(np.random.normal(0.0007, 0.012, 252))

    perf = PerformanceMetrics.calculate_all(returns)
    dsr_result = calculate_dsr(
        observed_sharpe=req.observed_sharpe,
        returns=returns,
        n_trials=req.n_trials,
    )
    sensitivity = SensitivityEngine.run_monte_carlo(returns)

    return {
        "performance": perf,
        "dsr": dsr_result,
        "sensitivity": sensitivity,
    }


@app.post("/api/simulate-backtest")
def simulate_backtest(req: AuditRequest) -> Dict[str, Any]:
    audit_res = analyzer.analyze_source(req.code)
    # Check if code is broken
    if not audit_res.is_valid_python:
        raise HTTPException(status_code=400, detail="Cannot backtest: Python Syntax Error present.")

    mock_resp = mock_server.handle_request({
        "method": "tools/call",
        "params": {
            "name": "run_backtest",
            "arguments": {"code": req.code},
        },
    })
    res_data = mock_resp.get("result", {})
    daily_returns = res_data.get("daily_returns", [])
    perf = PerformanceMetrics.calculate_all(daily_returns)
    dsr = calculate_dsr(observed_sharpe=perf.get("sharpe_ratio", 1.5), returns=daily_returns, n_trials=15)
    mc = SensitivityEngine.run_monte_carlo(daily_returns)

    # Compute equity curve points
    cum_equity = [100000.0]
    for r in daily_returns:
        cum_equity.append(cum_equity[-1] * (1.0 + r))

    return {
        "backtest_id": res_data.get("backtest_id"),
        "audit": audit_res.to_dict(),
        "performance": perf,
        "dsr": dsr,
        "sensitivity": mc,
        "equity_curve": [round(x, 2) for x in cum_equity],
    }


# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        alt_path = Path(__file__).resolve().parent.parent.parent / "public" / "index.html"
        if alt_path.exists():
            return FileResponse(alt_path)
    return FileResponse(index_path)

@app.get("/styles.css")
def serve_css():
    css_path = STATIC_DIR / "styles.css"
    if not css_path.exists():
        alt_path = Path(__file__).resolve().parent.parent.parent / "public" / "styles.css"
        if alt_path.exists():
            return FileResponse(alt_path, media_type="text/css")
    return FileResponse(css_path, media_type="text/css")

@app.get("/app.js")
def serve_js():
    js_path = STATIC_DIR / "app.js"
    if not js_path.exists():
        alt_path = Path(__file__).resolve().parent.parent.parent / "public" / "app.js"
        if alt_path.exists():
            return FileResponse(alt_path, media_type="application/javascript")
    return FileResponse(js_path, media_type="application/javascript")
