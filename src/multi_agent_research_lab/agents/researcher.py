"""Researcher agent implementation."""

from __future__ import annotations

import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        search_client: SearchClient | None = None,
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""

        start = time.perf_counter()
        query = getattr(state.request, "query", str(state.request))
        max_sources = getattr(state.request, "max_sources", 5)

        try:
            sources = self.search_client.search(query=query, max_results=max_sources)
            state.sources = sources

            source_context = "\n".join(
                [
                    f"- {source.title}: {source.snippet}"
                    + (f" URL: {source.url}" if source.url else "")
                    for source in sources
                ]
            )

            system_prompt = """
You are the Researcher Agent in a multi-agent research system.

Your job:
- Read the user query and available source snippets.
- Create concise research notes.
- Identify key concepts, useful evidence, and uncertainties.
- Do not write the final answer.
- Do not invent sources beyond the provided source snippets.

Return output in this structure:

## Research Notes
- ...

## Key Concepts
- ...

## Source-Based Evidence
- ...

## Uncertainties
- ...
""".strip()

            user_prompt = f"""
User research query:

{query}

Available source snippets:

{source_context}

Create research notes that will be passed to an Analyst Agent.
""".strip()

            response = self.llm_client.complete(system_prompt, user_prompt)
            state.research_notes = response.content

            state.add_trace_event(
                self.name,
                {
                    "status": "success",
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                    "source_count": len(sources),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )

        except Exception as exc:
            error_message = f"{self.name} failed: {exc}"
            state.errors.append(error_message)
            state.add_trace_event(
                self.name,
                {
                    "status": "error",
                    "error": error_message,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )

            state.research_notes = (
                "Researcher failed. Fallback note: no reliable research notes were generated."
            )

        return state