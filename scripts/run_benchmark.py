"""Run benchmark for baseline vs multi-agent workflow."""

from __future__ import annotations

import json
import time
from pathlib import Path

from dotenv import load_dotenv

from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import (
    run_benchmark,
    summarize_state,
)
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient


QUERIES = [
    "Research GraphRAG state-of-the-art and write a 500-word summary",
    "Compare single-agent and multi-agent systems for research tasks",
    "Explain common failure modes of multi-agent orchestration and how to fix them",
]


def run_baseline(query: str) -> ResearchState:
    """Run a single-agent baseline with one LLM call."""

    state = ResearchState(request=ResearchQuery(query=query))
    client = LLMClient()

    started = time.perf_counter()

    system_prompt = """
You are a single-agent research assistant.

Your job:
- Answer the user's research query directly.
- Include key findings, limitations, and a concise conclusion.
- Keep the answer clear and well-structured.
- Do not invent fake citations.
""".strip()

    user_prompt = f"""
User query:

{query}

Write the answer now.
""".strip()

    try:
        response = client.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        state.add_trace_event(
            "baseline",
            {
                "status": "success",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            },
        )

    except Exception as exc:
        state.errors.append(f"baseline failed: {exc}")
        state.add_trace_event(
            "baseline",
            {
                "status": "error",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": str(exc),
            },
        )

    return state


def run_multi_agent(query: str) -> ResearchState:
    """Run the multi-agent workflow."""

    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


def main() -> None:
    load_dotenv()

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    metrics = []
    run_summaries = []
    raw_results = []

    for idx, query in enumerate(QUERIES, start=1):
        benchmark_cases = [
            (f"q{idx}_baseline", run_baseline),
            (f"q{idx}_multi_agent", run_multi_agent),
        ]

        for run_name, runner in benchmark_cases:
            print(f"Running {run_name}...")

            state, item_metrics = run_benchmark(
                run_name=run_name,
                query=query,
                runner=runner,
            )

            metrics.append(item_metrics)

            summary = summarize_state(state)
            summary["run_name"] = run_name
            summary["query"] = query
            summary["routes"] = " -> ".join(state.route_history) if state.route_history else "none"

            run_summaries.append(summary)

            raw_results.append(
                {
                    "run_name": run_name,
                    "query": query,
                    "metrics": item_metrics.model_dump(),
                    "summary": summary,
                    "final_answer": state.final_answer,
                    "research_notes": state.research_notes,
                    "analysis_notes": state.analysis_notes,
                    "trace": state.trace,
                    "errors": state.errors,
                }
            )

    report_md = render_markdown_report(
        metrics=metrics,
        run_summaries=run_summaries,
        queries=QUERIES,
    )

    report_path = reports_dir / "benchmark_report.md"
    results_path = reports_dir / "benchmark_results.json"

    report_path.write_text(report_md, encoding="utf-8")
    results_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "benchmark_type": "single-agent vs multi-agent",
                    "query_count": len(QUERIES),
                    "run_count": len(raw_results),
                },
                "results": raw_results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Saved report to {report_path}")
    print(f"Saved raw results to {results_path}")


if __name__ == "__main__":
    main()