"""
Client for QuantConnect's Remote Model Context Protocol (MCP) Server.
Endpoint: https://www.quantconnect.com/api/v2/mcp
Enables agentic coding pipelines to validate, compile, and execute backtests.
"""

import json
from typing import Dict, Any, Optional
import httpx


class QuantConnectMCPClient:
    def __init__(self, endpoint_url: str = "https://www.quantconnect.com/api/v2/mcp", api_token: Optional[str] = None):
        self.endpoint_url = endpoint_url
        self.api_token = api_token

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "LeanSentinel/1.0.0",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call via Model Context Protocol JSON-RPC 2.0."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(self.endpoint_url, headers=self._headers(), json=payload)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {
                        "error": f"HTTP {resp.status_code}: {resp.text}",
                        "status_code": resp.status_code,
                    }
        except Exception as e:
            return {
                "error": f"Failed to connect to QuantConnect MCP Server: {str(e)}",
                "endpoint": self.endpoint_url,
            }

    def list_available_tools(self) -> Dict[str, Any]:
        """Query the remote server for available MCP capabilities."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.endpoint_url, headers=self._headers(), json=payload)
                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}
