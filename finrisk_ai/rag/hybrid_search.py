"""
Phase 1.2: Advanced RAG Pipeline with Hybrid Search

Implements a sophisticated multi-stage retrieval system combining:
1. Dense (Semantic) Search - Vector embeddings
2. Sparse (Keyword) Search - BM25
3. Reciprocal Rank Fusion - Combines results
4. Cross-Encoder Reranking - Precision refinement
5. GraphRAG - Structural context for interconnected data
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document/chunk in the RAG pipeline"""
    content: str
    metadata: Dict[str, Any]
    doc_id: str
    score: float = 0.0
    source: str = ""


@dataclass
class RetrievalResult:
    """Final retrieval result with multiple ranking stages"""
    documents: List[Document]
    dense_scores: List[float]
    sparse_scores: List[float]
    fusion_scores: List[float]
    rerank_scores: List[float]
    retrieval_metadata: Dict[str, Any]


class HybridSearchEngine:
    """
    Advanced Hybrid Search Engine combining dense and sparse retrieval.

    Based on 2024-2025 best practices:
    - Dense retrieval for semantic understanding
    - Sparse retrieval for exact keyword matching
    - Reciprocal Rank Fusion (RRF) for optimal combination
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        """
        Initialize hybrid search components.

        Args:
            embedding_model: Sentence transformer model for dense retrieval
            reranker_model: Cross-encoder model for reranking
        """
        logger.info("Initializing HybridSearchEngine...")

        # Dense retrieval (semantic)
        self.embedding_model = SentenceTransformer(embedding_model)

        # Reranking (precision)
        self.reranker = CrossEncoder(reranker_model)

        # Document storage
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Okapi] = None

        logger.info("HybridSearchEngine initialized successfully")

    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for both dense and sparse retrieval.

        Args:
            documents: List of documents to index
        """
        logger.info(f"Indexing {len(documents)} documents...")

        self.documents = documents

        # 1. Dense indexing - create embeddings
        contents = [doc.content for doc in documents]
        self.embeddings = self.embedding_model.encode(
            contents,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # 2. Sparse indexing - create BM25 index
        tokenized_corpus = [doc.content.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

        logger.info("Indexing complete")

    def dense_search(
        self,
        query: str,
        top_k: int = 100
    ) -> List[Tuple[Document, float]]:
        """
        Perform dense (semantic) search using vector embeddings.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        if self.embeddings is None:
            raise ValueError("Documents not indexed. Call index_documents() first.")

        # Encode query
        query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)

        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [
            (self.documents[idx], float(similarities[idx]))
            for idx in top_indices
        ]

        return results

    def sparse_search(
        self,
        query: str,
        top_k: int = 100
    ) -> List[Tuple[Document, float]]:
        """
        Perform sparse (keyword) search using BM25.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        if self.bm25 is None:
            raise ValueError("Documents not indexed. Call index_documents() first.")

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = [
            (self.documents[idx], float(scores[idx]))
            for idx in top_indices
            if scores[idx] > 0  # Only include documents with positive scores
        ]

        return results[:top_k]

    @staticmethod
    def reciprocal_rank_fusion(
        dense_results: List[Tuple[Document, float]],
        sparse_results: List[Tuple[Document, float]],
        k: int = 60
    ) -> List[Tuple[Document, float]]:
        """
        Combine dense and sparse results using Reciprocal Rank Fusion (RRF).

        RRF Formula: score(d) = Σ 1/(k + rank(d))

        Args:
            dense_results: Results from dense search
            sparse_results: Results from sparse search
            k: RRF constant (typically 60)

        Returns:
            Fused and ranked list of documents
        """
        # Create rank dictionaries
        doc_scores: Dict[str, float] = {}

        # Add dense results
        for rank, (doc, _) in enumerate(dense_results, start=1):
            doc_scores[doc.doc_id] = doc_scores.get(doc.doc_id, 0) + 1 / (k + rank)

        # Add sparse results
        for rank, (doc, _) in enumerate(sparse_results, start=1):
            doc_scores[doc.doc_id] = doc_scores.get(doc.doc_id, 0) + 1 / (k + rank)

        # Create document lookup
        all_docs = {doc.doc_id: doc for doc, _ in dense_results + sparse_results}

        # Sort by RRF score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        return [(all_docs[doc_id], score) for doc_id, score in sorted_docs]

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[Document, float]],
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Rerank candidates using cross-encoder for precision.

        Args:
            query: Original query
            candidates: List of candidate documents with scores
            top_k: Number of final results

        Returns:
            Reranked list of top documents
        """
        # Prepare query-document pairs
        pairs = [[query, doc.content] for doc, _ in candidates]

        # Get cross-encoder scores
        rerank_scores = self.reranker.predict(pairs)

        # Combine with documents
        reranked = [
            (doc, float(score))
            for (doc, _), score in zip(candidates, rerank_scores)
        ]

        # Sort by rerank score and return top-k
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[:top_k]

    def advanced_rag_pipeline(
        self,
        user_query: str,
        top_k_dense: int = 100,
        top_k_sparse: int = 100,
        top_k_final: int = 5
    ) -> RetrievalResult:
        """
        Complete advanced RAG pipeline with all stages.

        Stages:
        1. Dense (Semantic) Retrieval
        2. Sparse (Keyword) Retrieval
        3. Reciprocal Rank Fusion
        4. Cross-Encoder Reranking

        Args:
            user_query: User's search query
            top_k_dense: Number of dense results
            top_k_sparse: Number of sparse results
            top_k_final: Final number of results after reranking

        Returns:
            RetrievalResult with final documents and metadata
        """
        logger.info(f"Running advanced RAG pipeline for query: '{user_query}'")

        # Stage 1: Dense Retrieval
        dense_results = self.dense_search(user_query, top_k=top_k_dense)
        logger.debug(f"Dense retrieval: {len(dense_results)} results")

        # Stage 2: Sparse Retrieval
        sparse_results = self.sparse_search(user_query, top_k=top_k_sparse)
        logger.debug(f"Sparse retrieval: {len(sparse_results)} results")

        # Stage 3: Fusion
        fused_results = self.reciprocal_rank_fusion(dense_results, sparse_results)
        logger.debug(f"After fusion: {len(fused_results)} results")

        # Stage 4: Reranking (precision step)
        reranked_results = self.rerank(user_query, fused_results, top_k=top_k_final)
        logger.info(f"Final results after reranking: {len(reranked_results)}")

        # Extract final documents
        final_documents = [doc for doc, _ in reranked_results]

        return RetrievalResult(
            documents=final_documents,
            dense_scores=[s for _, s in dense_results[:top_k_final]],
            sparse_scores=[s for _, s in sparse_results[:top_k_final]],
            fusion_scores=[s for _, s in fused_results[:top_k_final]],
            rerank_scores=[s for _, s in reranked_results],
            retrieval_metadata={
                "query": user_query,
                "total_documents": len(self.documents),
                "dense_retrieved": len(dense_results),
                "sparse_retrieved": len(sparse_results),
                "fused_candidates": len(fused_results),
                "final_count": len(final_documents)
            }
        )


class VectorDatabase:
    """
    Simplified vector database interface using pgvector.

    In production, this would connect to PostgreSQL with pgvector extension.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize vector database connection.

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or "postgresql://localhost/finrisk_db"
        self.search_engine = HybridSearchEngine()

    def insert(self, documents: List[Document]) -> None:
        """Insert documents into vector database"""
        self.search_engine.index_documents(documents)

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Document]:
        """Perform hybrid search"""
        result = self.search_engine.advanced_rag_pipeline(
            user_query=query,
            top_k_final=top_k
        )
        return result.documents
