"""Optional critic agent for bonus review."""

from __future__ import annotations

import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append lightweight review findings."""

        start = time.perf_counter()
        findings: list[str] = []

        if not state.final_answer:
            findings.append("Final answer is missing.")
        else:
            answer = state.final_answer.lower()

            if "limitation" not in answer and "limitations" not in answer:
                findings.append("Final answer may not clearly discuss limitations.")

            if not state.sources:
                findings.append("No sources were attached to the research state.")

            if len(state.final_answer) < 500:
                findings.append("Final answer may be too short for a research summary.")

        if not findings:
            findings.append("No major issues detected by lightweight critic checks.")

        state.add_trace_event(
            self.name,
            {
                "status": "success",
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "findings": findings,
            },
        )

        return state