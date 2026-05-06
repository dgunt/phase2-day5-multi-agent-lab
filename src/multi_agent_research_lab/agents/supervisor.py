"""Supervisor / router implementation."""

from __future__ import annotations

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, max_iterations: int = 8) -> None:
        self.max_iterations = max_iterations

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Routing policy:
        - researcher runs first if research notes are missing.
        - analyst runs after research notes exist.
        - writer runs after analysis notes exist.
        - done when final answer exists.
        - done if max iteration guardrail is reached.
        """

        if state.iteration >= self.max_iterations:
            route = "done"
            state.errors.append(
                f"Max iterations reached: {state.iteration}/{self.max_iterations}"
            )

        elif not state.research_notes:
            route = "researcher"

        elif not state.analysis_notes:
            route = "analyst"

        elif not state.final_answer:
            route = "writer"

        else:
            route = "done"

        state.record_route(route)
        state.add_trace_event(
            self.name,
            {
                "status": "success",
                "selected_route": route,
                "iteration": state.iteration,
                "max_iterations": self.max_iterations,
            },
        )

        return state