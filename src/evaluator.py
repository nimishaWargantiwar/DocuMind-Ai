"""
RAG Evaluation system for measuring retrieval and answer quality.
Uses simple, interpretable metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass
class EvaluationResult:
    """Result from a single evaluation."""
    question: str
    retrieved_chunks: int
    answer_length: int
    response_time: float
    contains_query_words: bool
    has_grounding: bool  # Simple check: answer mentions document source info


@dataclass
class EvaluationMetrics:
    """Aggregated evaluation metrics."""
    questions_evaluated: int
    avg_response_time: float
    avg_retrieved_chunks: int
    retrieval_relevance: float  # 0-100, based on query word matching
    answer_relevance: float  # 0-100, based on query word coverage
    groundedness: float  # 0-100, based on sourcing
    
    def __str__(self) -> str:
        return f"""
RAG Evaluation Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Questions Evaluated:    {self.questions_evaluated}
Avg Response Time:      {self.avg_response_time:.2f}s
Avg Retrieved Chunks:   {self.avg_retrieved_chunks:.1f}
Retrieval Relevance:    {self.retrieval_relevance:.1f}%
Answer Relevance:       {self.answer_relevance:.1f}%
Groundedness Score:     {self.groundedness:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """


class RAGEvaluator:
    """Evaluates RAG system performance."""
    
    def __init__(self):
        self.results: list[EvaluationResult] = []
    
    def evaluate_response(
        self,
        question: str,
        answer: str,
        retrieved_chunks: int,
        response_time: float
    ) -> EvaluationResult:
        """Evaluate a single Q&A response."""
        
        # Check if answer contains key words from question
        question_words = set(question.lower().split())
        question_words = {w for w in question_words if len(w) > 3}  # Skip small words
        
        answer_lower = answer.lower()
        matching_words = sum(1 for w in question_words if w in answer_lower)
        contains_query = matching_words > 0
        
        # Check for grounding indicators
        has_grounding = any(phrase in answer_lower for phrase in [
            "page",
            "document",
            "based on",
            "according to",
            "states that",
            "mentioned in",
        ])
        
        result = EvaluationResult(
            question=question,
            retrieved_chunks=retrieved_chunks,
            answer_length=len(answer),
            response_time=response_time,
            contains_query_words=contains_query,
            has_grounding=has_grounding
        )
        
        self.results.append(result)
        return result
    
    def compute_metrics(self) -> EvaluationMetrics:
        """Compute aggregate metrics from all evaluations."""
        if not self.results:
            return EvaluationMetrics(
                questions_evaluated=0,
                avg_response_time=0.0,
                avg_retrieved_chunks=0.0,
                retrieval_relevance=0.0,
                answer_relevance=0.0,
                groundedness=0.0
            )
        
        n = len(self.results)
        
        # Calculate averages
        avg_response_time = sum(r.response_time for r in self.results) / n
        avg_retrieved_chunks = sum(r.retrieved_chunks for r in self.results) / n
        
        # Calculate relevance scores (0-100)
        answer_relevance = (sum(1 for r in self.results if r.contains_query_words) / n) * 100
        groundedness = (sum(1 for r in self.results if r.has_grounding) / n) * 100
        
        # Retrieval relevance based on number of chunks (more is better, up to a point)
        retrieval_relevance = min(100.0, (avg_retrieved_chunks / 4.0) * 100)
        
        return EvaluationMetrics(
            questions_evaluated=n,
            avg_response_time=avg_response_time,
            avg_retrieved_chunks=avg_retrieved_chunks,
            retrieval_relevance=retrieval_relevance,
            answer_relevance=answer_relevance,
            groundedness=groundedness
        )
    
    def reset(self) -> None:
        """Clear evaluation results."""
        self.results.clear()
    
    def create_test_questions(self) -> list[tuple[str, str]]:
        """Create sample test questions for evaluation."""
        # These are placeholder questions - should be customized per document
        return [
            ("What is the main topic of this document?", "general"),
            ("Who are the key people mentioned?", "entity"),
            ("What dates are discussed?", "temporal"),
            ("What are the main conclusions?", "summary"),
            ("What methodology or approach is used?", "method"),
        ]
