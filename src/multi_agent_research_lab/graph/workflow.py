"""Multi-agent workflow implementation.

This version keeps orchestration explicit and easy to debug.
A LangGraph implementation can be added later without changing agent internals.
"""

from __future__ import annotations

import time
from typing import Callable

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self, max_iterations: int = 8) -> None:
        self.max_iterations = max_iterations
        self.supervisor = SupervisorAgent(max_iterations=max_iterations)
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

    def build(self) -> dict[str, Callable[[ResearchState], ResearchState]]:
        """Create a simple graph-like mapping of route names to agent nodes.

        This is intentionally simple for the lab MVP. It still follows the same
        orchestration idea as a LangGraph workflow: route -> node -> updated state.
        """

        return {
            "supervisor": self.supervisor.run,
            "researcher": self.researcher.run,
            "analyst": self.analyst.run,
            "writer": self.writer.run,
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the workflow and return final state."""

        start = time.perf_counter()
        graph = self.build()

        state.add_trace_event(
            "workflow",
            {
                "status": "started",
                "max_iterations": self.max_iterations,
            },
        )

        while state.iteration < self.max_iterations:
            state = graph["supervisor"](state)

            if not state.route_history:
                state.errors.append("Supervisor did not produce a route.")
                break

            next_route = state.route_history[-1]

            if next_route == "done":
                break

            node = graph.get(next_route)
            if node is None:
                state.errors.append(f"Unknown route selected by supervisor: {next_route}")
                break

            state = node(state)

        if state.iteration >= self.max_iterations and not state.final_answer:
            state.errors.append(
                f"Workflow stopped because max_iterations={self.max_iterations} was reached."
            )

        state.add_trace_event(
            "workflow",
            {
                "status": "completed" if state.final_answer else "incomplete",
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "routes": state.route_history,
                "has_final_answer": state.final_answer is not None,
                "error_count": len(state.errors),
            },
        )

        return state