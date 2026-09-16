"""Call a locally running TokenNexus application over HTTP."""

from __future__ import annotations

import argparse
import http.client
import json


def request_json(
    connection: http.client.HTTPConnection,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    """Send one JSON request and return its status and decoded body."""
    body = json.dumps(payload) if payload is not None else None
    headers = {"Content-Type": "application/json", "X-Scope-Id": "local-smoke-test"}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    document = json.loads(response.read().decode("utf-8"))
    return response.status, document


def create_parser() -> argparse.ArgumentParser:
    """Create command-line arguments for the smoke client."""
    parser = argparse.ArgumentParser(description="Call the local TokenNexus HTTP app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser


def main() -> int:
    """Verify health and execute one governed local request."""
    arguments = create_parser().parse_args()
    connection = http.client.HTTPConnection(arguments.host, arguments.port, timeout=5)
    try:
        health_status, health = request_json(connection, "GET", "/health")
        if health_status != 200 or health.get("status") != "ok":
            raise RuntimeError(f"health check failed: HTTP {health_status}: {health}")

        execute_status, result = request_json(
            connection,
            "POST",
            "/v1/execute",
            {
                "schema_version": "1.0.0",
                "idempotency_key": "local-http-example",
                "application_id": "local-smoke-client",
                "task": {"content": "Explain how TokenNexus saves tokens."},
            },
        )
        if execute_status != 200 or result.get("status") != "completed":
            raise RuntimeError(f"execution failed: HTTP {execute_status}: {result}")
        print(json.dumps(result, indent=2))
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())