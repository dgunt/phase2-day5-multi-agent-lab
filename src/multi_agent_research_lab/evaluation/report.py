"""Benchmark report rendering."""

from __future__ import annotations

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(
    metrics: list[BenchmarkMetrics],
    run_summaries: list[dict[str, object]] | None = None,
    queries: list[str] | None = None,
) -> str:
    """Render benchmark metrics to markdown."""

    run_summaries = run_summaries or []
    queries = queries or []

    lines: list[str] = [
        "# Benchmark Report - Multi-Agent Research Lab",
        "",
        "## 1. Objective",
        "",
        (
            "This report compares a single-agent baseline with a multi-agent "
            "workflow composed of Supervisor, Researcher, Analyst, and Writer agents."
        ),
        "",
        "## 2. Benchmark Queries",
        "",
    ]

    if queries:
        for idx, query in enumerate(queries, start=1):
            lines.append(f"{idx}. `{query}`")
    else:
        lines.append("- No query list provided.")

    lines.extend(
        [
            "",
            "## 3. Metrics",
            "",
            "| Run | Latency (s) | Estimated Cost (USD) | Quality | Notes |",
            "|---|---:|---:|---:|---|",
        ]
    )

    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        notes = item.notes.replace("|", "/")
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {notes} |"
        )

    lines.extend(
        [
            "",
            "## 4. Run Summaries",
            "",
            "| Run | Routes | Trace Events | Errors | Input Tokens | Output Tokens | Final Answer Chars |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )

    for summary in run_summaries:
        lines.append(
            "| {run_name} | {routes} | {trace_events} | {error_count} | "
            "{input_tokens} | {output_tokens} | {final_answer_chars} |".format(
                run_name=summary.get("run_name", ""),
                routes=summary.get("routes", "none"),
                trace_events=summary.get("trace_events", 0),
                error_count=summary.get("error_count", 0),
                input_tokens=summary.get("input_tokens", 0),
                output_tokens=summary.get("output_tokens", 0),
                final_answer_chars=summary.get("final_answer_chars", 0),
            )
        )

    lines.extend(
        [
            "",
            "## 5. Analysis",
            "",
            (
                "The single-agent baseline is faster because it uses one LLM call to perform "
                "research, analysis, and writing in a single step. However, this makes the "
                "reasoning process less observable."
            ),
            "",
            (
                "The multi-agent workflow is slower and slightly more expensive because it "
                "uses multiple LLM calls. In exchange, it provides clearer role separation, "
                "better traceability, and intermediate artifacts such as research notes and "
                "analysis notes."
            ),
            "",
            "## 6. Failure Modes and Fixes",
            "",
            "### Failure Mode 1: Researcher returns vague notes",
            "- **Cause:** The research prompt is too broad or lacks source grounding.",
            "- **Fix:** Add external search integration and require structured notes with evidence.",
            "",
            "### Failure Mode 2: Analyst repeats researcher notes",
            "- **Cause:** Weak role separation between Researcher and Analyst.",
            "- **Fix:** Force Analyst to focus on claims, trade-offs, weak evidence, and risks.",
            "",
            "### Failure Mode 3: Writer ignores length or structure requirements",
            "- **Cause:** No output validation after generation.",
            "- **Fix:** Add validation for word count, sections, and citation/source coverage.",
            "",
            "### Failure Mode 4: Cost and latency increase in multi-agent mode",
            "- **Cause:** Multi-agent workflow uses several LLM calls instead of one.",
            "- **Fix:** Use smaller models for intermediate agents, cache research notes, and stop early when enough information is available.",
            "",
            "## 7. Conclusion",
            "",
            (
                "The multi-agent approach is more suitable for complex research tasks where "
                "traceability, decomposition, and intermediate reasoning are important. For "
                "simple tasks, the single-agent baseline remains faster and cheaper."
            ),
            "",
        ]
    )

    return "\n".join(lines)