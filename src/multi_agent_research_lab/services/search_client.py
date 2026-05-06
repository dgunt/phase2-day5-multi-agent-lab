"""Search client abstraction for ResearcherAgent.

This implementation provides a deterministic local mock search so the lab can
run without requiring Tavily, Bing, SerpAPI, or external search credentials.
"""

from __future__ import annotations

from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client with local mock fallback."""

    def __init__(self) -> None:
        self.local_corpus = [
            SourceDocument(
                title="GraphRAG Overview",
                url="https://www.microsoft.com/en-us/research/project/graphrag/",
                snippet=(
                    "GraphRAG combines retrieval-augmented generation with graph-based "
                    "representations to improve global understanding over large document collections."
                ),
                metadata={"source_type": "mock", "topic": "GraphRAG"},
            ),
            SourceDocument(
                title="Retrieval-Augmented Generation",
                url="https://arxiv.org/abs/2005.11401",
                snippet=(
                    "RAG improves language generation by retrieving external context "
                    "and grounding model responses in relevant documents."
                ),
                metadata={"source_type": "mock", "topic": "RAG"},
            ),
            SourceDocument(
                title="Multi-Agent System Design",
                url=None,
                snippet=(
                    "Multi-agent workflows decompose complex tasks into specialized "
                    "roles such as planning, research, analysis, writing, and review."
                ),
                metadata={"source_type": "mock", "topic": "multi-agent"},
            ),
            SourceDocument(
                title="Agent Orchestration and Handoffs",
                url=None,
                snippet=(
                    "A supervisor or router can coordinate worker agents, maintain "
                    "shared state, and prevent infinite loops through guardrails."
                ),
                metadata={"source_type": "mock", "topic": "orchestration"},
            ),
            SourceDocument(
                title="AI Evaluation and Benchmarking",
                url=None,
                snippet=(
                    "Benchmarking agent systems should include quality, latency, cost, "
                    "traceability, error rate, and failure-mode analysis."
                ),
                metadata={"source_type": "mock", "topic": "evaluation"},
            ),
        ]

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Current version uses a local mock corpus. This keeps the lab reproducible
        without external search API keys.
        """

        normalized_query = query.lower()
        scored_results: list[tuple[int, SourceDocument]] = []

        for document in self.local_corpus:
            haystack = f"{document.title} {document.snippet}".lower()
            score = 0

            for term in normalized_query.split():
                if term in haystack:
                    score += 1

            if score > 0:
                scored_results.append((score, document))

        if not scored_results:
            return self.local_corpus[:max_results]

        scored_results.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored_results[:max_results]]