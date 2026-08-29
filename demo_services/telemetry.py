import time
import uuid
from typing import Callable, Optional
from fastapi import FastAPI, Request
from runtime import RuntimeEngine, RuntimeObservation

runtime_engine = RuntimeEngine()

def setup_telemetry(app: FastAPI, service_name: str):
    @app.middleware("http")
    async def otel_tracing_middleware(request: Request, call_next: Callable):
        start_time = time.time()
        trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex
        parent_span_id = request.headers.get("x-span-id")
        span_id = uuid.uuid4().hex[:16]

        caller_service = request.headers.get("x-caller-service") or "external"

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000.0
        status_code = response.status_code
        is_error = status_code >= 400

        operation = f"{request.method} {request.url.path}"

        # Record observation
        obs = RuntimeObservation(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            source_service=caller_service,
            destination_service=service_name,
            operation=operation,
            duration_ms=round(duration_ms, 2),
            status_code=status_code,
            is_error=is_error,
            timestamp=time.time()
        )
        runtime_engine.record_trace(obs)

        # Propagate trace headers to client
        response.headers["x-trace-id"] = trace_id
        response.headers["x-span-id"] = span_id
        return response
