"""Tests for implemented agents."""

from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))

    result = SupervisorAgent().run(state)

    assert result.route_history[-1] == "researcher"
    assert result.iteration == 1


def test_supervisor_routes_to_analyst_after_research() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="Some research notes.",
    )

    result = SupervisorAgent().run(state)

    assert result.route_history[-1] == "analyst"


def test_supervisor_routes_to_writer_after_analysis() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="Some research notes.",
        analysis_notes="Some analysis notes.",
    )

    result = SupervisorAgent().run(state)

    assert result.route_history[-1] == "writer"


def test_supervisor_routes_to_done_after_final_answer() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="Some research notes.",
        analysis_notes="Some analysis notes.",
        final_answer="Final answer.",
    )

    result = SupervisorAgent().run(state)

    assert result.route_history[-1] == "done"