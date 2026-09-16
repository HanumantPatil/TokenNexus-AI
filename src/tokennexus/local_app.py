"""Dependency-free local HTTP host for the deterministic TokenNexus demo."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar
from uuid import UUID

from pydantic import ValidationError

from tokennexus.contracts import (
    Money,
    NormalizedRequest,
    Output,
    QualitySummary,
    Usage,
    parse_public_request_json,
)
from tokennexus.coordinator import Coordinator
from tokennexus.journal import InMemoryJournal
from tokennexus.ports import (
    ModelAlias,
    ModelInvocation,
    ModelOutcome,
    ModelOutcomeStatus,
    NeverCancelled,
    SystemClock,
    Uuid7Source,
)
from tokennexus.problem_details import (
    domain_error_from_validation,
    problem_details_from_domain_error,
)

MAX_REQUEST_BYTES = 1_000_000


class LocalBudget:
    """Allow all reservations for local deterministic execution."""

    def reserve(
        self,
        *,
        request_id: UUID,
        operation_key: str,
        estimated_cost: Money,
    ) -> bool:
        del request_id, operation_key, estimated_cost
        return True


class LocalModel:
    """Return a deterministic response without calling an external provider."""

    def estimate_cost(self, request: NormalizedRequest, model_alias: ModelAlias) -> Money:
        del request, model_alias
        return Money(amount="0.01")

    def invoke(self, invocation: ModelInvocation) -> ModelOutcome:
        task = invocation.request.task.content
        return ModelOutcome(
            status=ModelOutcomeStatus.SUCCEEDED,
            output=Output(content=f"Local deterministic response: {task}"),
            usage=Usage(
                input_tokens=len(task.split()),
                output_tokens=len(task.split()) + 3,
                estimated_cost=Money(amount="0.01"),
                provider_latency_ms=0,
            ),
        )


class LocalQualityEvaluator:
    """Pass deterministic local outputs without an external evaluator."""

    def estimate_cost(self, request: NormalizedRequest, output: Output) -> Money:
        del request, output
        return Money(amount="0")

    def evaluate(self, request: NormalizedRequest, output: Output) -> QualitySummary:
        del output
        return QualitySummary(
            status="passed",
            score="5",
            threshold=request.effective_constraints.minimum_quality,
        )


def create_coordinator() -> Coordinator:
    """Create the process-local deterministic application composition root."""
    return Coordinator(
        journal=InMemoryJournal(),
        budget=LocalBudget(),
        model=LocalModel(),
        quality=LocalQualityEvaluator(),
        cancellation=NeverCancelled(),
        clock=SystemClock(),
        ids=Uuid7Source(),
    )


class LocalRequestHandler(BaseHTTPRequestHandler):
    """Expose health and governed execution endpoints over local HTTP."""

    coordinator: ClassVar[Coordinator]
    server_version = "TokenNexusLocal/0.1"

    def do_GET(self) -> None:
        if self.path != "/health":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        self._write_json(HTTPStatus.OK, {"status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/v1/execute":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        content_length = self._content_length()
        if content_length is None:
            return
        try:
            request = parse_public_request_json(self.rfile.read(content_length))
        except ValidationError as error:
            problem = problem_details_from_domain_error(domain_error_from_validation(error))
            self._write_json(HTTPStatus.BAD_REQUEST, problem.model_dump(mode="json"))
            return
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self._write_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_json", "detail": "Request body must be valid JSON."},
            )
            return

        scope_id = self.headers.get("X-Scope-Id", "local")
        result = self.coordinator.execute(request, scope_id=scope_id)
        self._write_json(HTTPStatus.OK, result.model_dump(mode="json"))

    def log_message(self, message_format: str, *args: object) -> None:
        print(f"{self.address_string()} - {message_format % args}")

    def _content_length(self) -> int | None:
        value = self.headers.get("Content-Length")
        try:
            content_length = int(value) if value is not None else -1
        except ValueError:
            content_length = -1
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            self._write_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid_content_length"},
            )
            return None
        return content_length

    def _write_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str, port: int) -> ThreadingHTTPServer:
    """Create a local HTTP server with one shared coordinator."""
    LocalRequestHandler.coordinator = create_coordinator()
    return ThreadingHTTPServer((host, port), LocalRequestHandler)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line arguments for the local host."""
    parser = argparse.ArgumentParser(description="Run the local TokenNexus HTTP demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser


def main() -> int:
    """Run the local server until interrupted."""
    arguments = create_parser().parse_args()
    server = create_server(arguments.host, arguments.port)
    print(f"TokenNexus local app listening on http://{arguments.host}:{arguments.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping TokenNexus local app")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())