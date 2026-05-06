"""Base agent contract.

All concrete agents implement this interface and update the shared ResearchState.
"""

from abc import ABC, abstractmethod

from multi_agent_research_lab.core.state import ResearchState


class BaseAgent(ABC):
    """Minimal interface every agent must implement."""

    name: str

    @abstractmethod
    def run(self, state: ResearchState) -> ResearchState:
        """Read and update shared state, then return it."""