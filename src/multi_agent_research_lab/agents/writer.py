"""Writer agent implementation."""

from __future__ import annotations

import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        start = time.perf_counter()
        query = getattr(state.request, "query", str(state.request))
        research_notes = state.research_notes or "No research notes were provided."
        analysis_notes = state.analysis_notes or "No analysis notes were provided."

        system_prompt = """
You are the Writer Agent in a multi-agent research system.

Your job:
- Write the final answer for the user.
- Use the research notes and analysis notes.
- Be clear, structured, and accurate.
- Mention limitations when evidence is weak.
- Do not invent citations or fake sources.
- If the user asks for a word limit, try to follow it.

Return a polished final answer.
""".strip()

        user_prompt = f"""
Original user query:

{query}

Research notes:

{research_notes}

Analysis notes:

{analysis_notes}

Write the final answer now.
""".strip()

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            state.final_answer = response.content

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

            state.final_answer = (
                "The Writer Agent failed to generate a final answer. "
                "Please inspect the trace and errors for details."
            )

        return state