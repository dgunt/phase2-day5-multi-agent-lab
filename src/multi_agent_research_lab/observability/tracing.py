"""Tracing hooks.

This file intentionally avoids binding to one provider. The current implementation
uses a lightweight local span that can later be connected to LangSmith, Langfuse,
OpenTelemetry, or JSON trace export.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the workflow and agents."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "status": "started",
    }

    try:
        yield span
        span["status"] = "success"
    except Exception as exc:
        span["status"] = "error"
        span["error"] = str(exc)
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started