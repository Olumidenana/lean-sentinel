"""
Offline Mock MCP Server for QuantConnect LEAN.
Provides local simulation for testing, unit tests, and demoing without live cloud credentials.
"""

from typing import Dict, Any
import numpy as np


class MockQuantConnectMCPServer:
    """
    Simulates the QuantConnect remote MCP endpoint for offline agent orchestration.
    """

    AVAILABLE_TOOLS = [
        {"name": "create_project", "description": "Create a new QuantConnect cloud project."},
        {"name": "read_file", "description": "Read file contents within a project."},
        {"name": "write_file", "description": "Write or update code files."},
        {"name": "compile_project", "description": "Compile the algorithm and check for C#/Python errors."},
        {"name": "run_backtest", "description": "Queue and execute a backtest in the cloud."},
        {"name": "get_backtest_results", "description": "Fetch tearsheet metrics, orders, and equity curves."},
    ]

    def handle_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        method = payload.get("method")
        params = payload.get("params", {})
        req_id = payload.get("id", 1)

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.AVAILABLE_TOOLS},
            }

        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})

            if tool_name == "compile_project":
                code = args.get("code", "")
                if "SyntaxError" in code or "def (" in code:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"success": False, "errors": ["Compiler Error: Invalid syntax at line 14"]},
                    }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"success": True, "status": "Compiled successfully", "warnings": []},
                }

            if tool_name == "run_backtest":
                # Generate realistic simulation equity curve
                np.random.seed(42)
                daily_returns = np.random.normal(0.0006, 0.012, 252)  # positive drift
                cum_ret = np.cumprod(1.0 + daily_returns)
                total_return = float(cum_ret[-1] - 1.0)

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "backtest_id": "backtest_qc_sim_98231",
                        "status": "Completed",
                        "statistics": {
                            "Total Return": f"{round(total_return * 100, 2)}%",
                            "Sharpe Ratio": "1.742",
                            "Sortino Ratio": "2.108",
                            "Max Drawdown": "-7.4%",
                            "Win Rate": "58.3%",
                            "Profit Loss Ratio": "1.82",
                            "Total Trades": 142,
                        },
                        "daily_returns": [float(r) for r in daily_returns],
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method or tool not found."},
        }
