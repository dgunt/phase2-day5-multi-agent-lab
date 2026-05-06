"""Analyst agent implementation."""

from __future__ import annotations

import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""

        start = time.perf_counter()
        query = getattr(state.request, "query", str(state.request))
        research_notes = state.research_notes or "No research notes were provided."

        system_prompt = """
You are the Analyst Agent in a multi-agent research system.

Your job:
- Analyze the research notes.
- Extract key claims.
- Compare viewpoints if relevant.
- Identify trade-offs, risks, weak evidence, and gaps.
- Do not write the final answer.

Return output in this structure:

## Key Claims
- ...

## Analysis
- ...

## Trade-offs / Risks
- ...

## Weak Evidence or Gaps
- ...

## Recommendation for Writer
- ...
""".strip()

        user_prompt = f"""
Original user query:

{query}

Research notes from Researcher Agent:

{research_notes}

Analyze these notes for the Writer Agent.
""".strip()

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            state.analysis_notes = response.content

            state.add_trace_event(
                self.name,
                {
                    "status": "success",
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
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

            state.analysis_notes = (
                "Analyst failed to call the LLM. "
                "Fallback analysis: use the available research notes directly."
            )

        return state