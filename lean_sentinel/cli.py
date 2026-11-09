"""
Command-Line Interface for LeanSentinel.
Usage:
  lean-sentinel audit <file.py>
  lean-sentinel fix <file.py>
  lean-sentinel synthesize --type momentum
  lean-sentinel dsr --sharpe 1.85 --trials 50
  lean-sentinel serve --port 8000
"""

import sys
import os
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import click
import uvicorn

from lean_sentinel.linter.analyzer import LeanASTAnalyzer
from lean_sentinel.linter.reporter import LeanReporter
from lean_sentinel.synthesizer.generator import LeanFrameworkSynthesizer
from lean_sentinel.statistics.dsr import calculate_dsr
import numpy as np


@click.group()
@click.version_option(version="1.0.0", prog_name="lean-sentinel")
def main():
    """LeanSentinel: QuantConnect AI Agent Supervisor & Linter CLI."""
    pass


@main.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False))
@click.option("--format", "-f", type=click.Choice(["text", "markdown", "json"]), default="text")
def audit(filepath: str, format: str):
    """Audit a QuantConnect Python algorithm for anti-patterns and hallucinations."""
    content = Path(filepath).read_text(encoding="utf-8")
    analyzer = LeanASTAnalyzer()
    res = analyzer.analyze_source(content, filename=Path(filepath).name)

    if format == "markdown":
        click.echo(LeanReporter.to_markdown(res))
    elif format == "json":
        click.echo(LeanReporter.to_json(res))
    else:
        click.echo(LeanReporter.to_cli_text(res))

    # Exit code based on critical findings
    if res.critical_count > 0:
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", type=click.Path(dir_okay=False), default=None)
def fix(filepath: str, output: str):
    """Apply surgical auto-remediation to common LEAN anti-patterns."""
    content = Path(filepath).read_text(encoding="utf-8")
    remediated = LeanFrameworkSynthesizer.sanitize_monolithic(content)
    target_path = output or filepath
    Path(target_path).write_text(remediated, encoding="utf-8")
    click.echo(f"✓ Successfully remediated algorithm saved to: {target_path}")


@main.command()
@click.option("--type", "-t", type=click.Choice(["momentum", "mean_reversion"]), default="momentum")
@click.option("--symbols", "-s", default="SPY,QQQ,IWM", help="Comma-separated symbols")
@click.option("--output", "-o", default="algorithm.py", help="Output file path")
def synthesize(type: str, symbols: str, output: str):
    """Synthesize a canonical 5-component QuantConnect Framework algorithm."""
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    code = LeanFrameworkSynthesizer.generate(strategy_type=type, symbols=sym_list)
    Path(output).write_text(code, encoding="utf-8")
    click.echo(f"✓ Generated 5-component QC Algorithm Framework ({type}) -> {output}")


@main.command()
@click.option("--sharpe", "-s", type=float, required=True, help="Observed Annualized Sharpe Ratio")
@click.option("--trials", "-n", type=int, default=25, help="Number of backtest / prompt iterations")
def dsr(sharpe: float, trials: int):
    """Calculate Deflated Sharpe Ratio (DSR) and Haircut Sharpe."""
    np.random.seed(42)
    sample_returns = list(np.random.normal(0.0006, 0.012, 252))
    res = calculate_dsr(observed_sharpe=sharpe, returns=sample_returns, n_trials=trials)

    click.echo("=" * 60)
    click.echo("  DEFLATED SHARPE RATIO (DSR) EVALUATION")
    click.echo("=" * 60)
    click.echo(f"  Observed Sharpe:              {res['observed_sharpe']}")
    click.echo(f"  Trials Evaluated (N):         {res['n_trials_evaluated']}")
    click.echo(f"  Expected Max Null Sharpe:     {res['expected_max_null_sharpe']}")
    click.echo(f"  DSR Probability:              {res['dsr_probability'] * 100:.1f}%")
    click.echo(f"  Haircut Sharpe Ratio:         {res['haircut_sharpe_ratio']}")
    click.echo(f"  Overfitting Risk Level:       {res['overfitting_risk']}")
    click.echo(f"  Statistically Significant:    {'YES (p > 0.95)' if res['is_statistically_significant'] else 'NO (High probability of data snooping)'}")
    click.echo("=" * 60)


@main.command()
@click.option("--port", "-p", type=int, default=8000, help="Port to serve studio")
@click.option("--host", "-h", default="127.0.0.1", help="Host address")
def serve(host: str, port: int):
    """Launch the interactive LeanSentinel Web Studio."""
    click.echo(f"🛡️  Starting LeanSentinel Studio on http://{host}:{port}")
    uvicorn.run("lean_sentinel.web.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
