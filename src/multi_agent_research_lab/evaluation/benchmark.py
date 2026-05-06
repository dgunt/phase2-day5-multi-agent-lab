"""Benchmark utilities for single-agent vs multi-agent runs."""

from __future__ import annotations

import os
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def extract_token_usage(state: ResearchState) -> tuple[int, int]:
    """Extract total input/output tokens from trace events."""

    total_input_tokens = 0
    total_output_tokens = 0

    for event in state.trace:
        payload = event.get("payload", {})
        input_tokens = payload.get("input_tokens")
        output_tokens = payload.get("output_tokens")

        if isinstance(input_tokens, int):
            total_input_tokens += input_tokens

        if isinstance(output_tokens, int):
            total_output_tokens += output_tokens

    return total_input_tokens, total_output_tokens


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Estimate LLM cost from token usage.

    These are lab-level estimates. For production, replace them with the
    exact pricing of the model/provider used in your account.
    """

    input_cost_per_1k = float(os.getenv("LLM_INPUT_COST_PER_1K", "0.00015"))
    output_cost_per_1k = float(os.getenv("LLM_OUTPUT_COST_PER_1K", "0.00060"))

    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k

    return round(input_cost + output_cost, 6)


def heuristic_quality_score(state: ResearchState) -> float:
    """Estimate answer quality with a simple transparent heuristic.

    This is not a replacement for human or LLM-as-judge evaluation.
    It is enough for a lab benchmark where we need a repeatable baseline.
    """

    score = 5.0
    answer = state.final_answer or ""

    if len(answer) >= 800:
        score += 1.0

    if len(answer) >= 1500:
        score += 0.5

    lower_answer = answer.lower()

    structure_markers = ["#", "key", "limitation", "conclusion", "summary"]
    if any(marker in lower_answer for marker in structure_markers):
        score += 1.0

    if state.research_notes:
        score += 0.75

    if state.analysis_notes:
        score += 0.75

    if state.route_history:
        score += 0.5

    if state.errors:
        score -= min(2.0, len(state.errors) * 0.75)

    if not answer.strip():
        score = 0.0

    return round(max(0.0, min(10.0, score)), 1)


def summarize_state(state: ResearchState) -> dict[str, object]:
    """Create a compact state summary for JSON reports."""

    input_tokens, output_tokens = extract_token_usage(state)

    return {
        "route_history": state.route_history,
        "iteration": state.iteration,
        "trace_events": len(state.trace),
        "error_count": len(state.errors),
        "errors": state.errors,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimate_cost_usd(input_tokens, output_tokens),
        "has_research_notes": state.research_notes is not None,
        "has_analysis_notes": state.analysis_notes is not None,
        "has_final_answer": state.final_answer is not None,
        "final_answer_chars": len(state.final_answer or ""),
    }


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Run a benchmark case and return state + metrics."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    input_tokens, output_tokens = extract_token_usage(state)
    estimated_cost = estimate_cost_usd(input_tokens, output_tokens)
    quality_score = heuristic_quality_score(state)

    route_text = "->".join(state.route_history) if state.route_history else "none"

    notes = (
        f"input_tokens={input_tokens}; "
        f"output_tokens={output_tokens}; "
        f"errors={len(state.errors)}; "
        f"routes={route_text}"
    )

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality_score,
        notes=notes,
    )

    return state, metrics