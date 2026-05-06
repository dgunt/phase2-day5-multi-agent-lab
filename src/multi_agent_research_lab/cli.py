"""Command-line entrypoint for the lab."""

from __future__ import annotations

import time
from typing import Annotated
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()


def _init() -> None:
    load_dotenv()
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline using one LLM call."""

    _init()
    start = time.perf_counter()

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
        client = LLMClient()
        response = client.complete(system_prompt, user_prompt)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        console.print(
            Panel.fit(
                response.content,
                title="Single-Agent Baseline",
                border_style="blue",
            )
        )

        table = Table(title="Baseline Metrics")
        table.add_column("Metric")
        table.add_column("Value")

        table.add_row("latency_ms", str(latency_ms))
        table.add_row("input_tokens", str(response.input_tokens))
        table.add_row("output_tokens", str(response.output_tokens))
        table.add_row("cost_usd", str(response.cost_usd))

        console.print(table)

    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Setup Error", style="yellow"))
        raise typer.Exit(code=2) from exc

    except Exception as exc:
        console.print(Panel.fit(str(exc), title="Baseline Error", style="red"))
        raise typer.Exit(code=1) from exc


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()

    try:
        result = workflow.run(state)

    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Setup Error", style="yellow"))
        raise typer.Exit(code=2) from exc

    except Exception as exc:
        console.print(Panel.fit(str(exc), title="Multi-Agent Error", style="red"))
        raise typer.Exit(code=1) from exc

    console.print(
        Panel.fit(
            result.final_answer or "No final answer generated.",
            title="Multi-Agent Final Answer",
            border_style="green",
        )
    )

    route_text = " → ".join(result.route_history)

    table = Table(title="Multi-Agent Run Summary")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("routes", route_text)
    table.add_row("iterations", str(result.iteration))
    table.add_row("trace_events", str(len(result.trace)))
    table.add_row("errors", str(len(result.errors)))

    console.print(table)

    if result.errors:
        console.print(
            Panel.fit(
                "\n".join(result.errors),
                title="Errors",
                border_style="red",
            )
        )

    console.print(
        Panel.fit(
            result.model_dump_json(indent=2),
            title="Full State JSON",
            border_style="dim",
        )
    )


if __name__ == "__main__":
    app()