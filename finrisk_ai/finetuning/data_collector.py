"""
Phase 5.1: Training Data Collection

Collects high-quality training examples from production API usage
for fine-tuning Gemini models.

Captures:
- User queries
- RAG context retrieved
- C++ calculation results
- AI-generated responses
- Quality validation scores
- User feedback (if available)
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """A single training example for fine-tuning"""

    # Input
    user_query: str
    rag_context: List[str]
    user_preferences: Dict[str, Any]
    calculation_task: str

    # Output
    calculation_selection: Dict[str, Any]  # Which C++ functions selected
    calculation_results: Dict[str, Any]
    narrative_response: str

    # Metadata
    quality_score: float  # 0.0-1.0 from validation agent
    timestamp: str
    user_id: str
    session_id: str

    # Optional feedback
    user_feedback: Optional[str] = None
    user_rating: Optional[int] = None  # 1-5 stars

    def to_gemini_format(self) -> Dict[str, Any]:
        """
        Convert to Gemini fine-tuning format.

        Format: {"text_input": "...", "output": "..."}
        """
        # Construct rich input context
        input_parts = [
            f"USER QUERY: {self.user_query}",
            "",
            "USER PREFERENCES:",
            f"- Risk Tolerance: {self.user_preferences.get('risk_tolerance', 'moderate')}",
            f"- Reporting Style: {self.user_preferences.get('reporting_style', 'detailed')}",
            "",
            "RELEVANT KNOWLEDGE:",
        ]

        for i, context in enumerate(self.rag_context[:5], 1):  # Top 5 context
            input_parts.append(f"{i}. {context}")

        input_parts.extend([
            "",
            "CALCULATION TASK:",
            self.calculation_task,
            "",
            "YOUR TASK: Select appropriate C++ functions and generate a narrative response.",
        ])

        # Construct output with function selection + narrative
        output_parts = [
            "FUNCTION SELECTION:",
            json.dumps(self.calculation_selection, indent=2),
            "",
            "NARRATIVE RESPONSE:",
            self.narrative_response,
        ]

        return {
            "text_input": "\n".join(input_parts),
            "output": "\n".join(output_parts),
        }

    def get_hash(self) -> str:
        """Generate unique hash for deduplication"""
        content = f"{self.user_query}:{self.calculation_task}:{self.narrative_response}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class TrainingDataCollector:
    """
    Collects and stores training examples from production usage.

    Features:
    - Async collection (non-blocking for API)
    - Quality filtering (only high-quality examples)
    - Deduplication
    - Privacy controls
    - Batch persistence
    """

    def __init__(
        self,
        storage_path: str = "data/training_examples",
        quality_threshold: float = 0.8,
        enable_privacy_filter: bool = True,
        batch_size: int = 100,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.quality_threshold = quality_threshold
        self.enable_privacy_filter = enable_privacy_filter
        self.batch_size = batch_size

        self.current_batch: List[TrainingExample] = []
        self.seen_hashes = set()

        logger.info(f"TrainingDataCollector initialized at {storage_path}")
        logger.info(f"Quality threshold: {quality_threshold}")

    def collect_example(
        self,
        user_query: str,
        rag_context: List[str],
        user_preferences: Dict[str, Any],
        calculation_task: str,
        calculation_selection: Dict[str, Any],
        calculation_results: Dict[str, Any],
        narrative_response: str,
        quality_score: float,
        user_id: str,
        session_id: str,
        user_feedback: Optional[str] = None,
        user_rating: Optional[int] = None,
    ) -> bool:
        """
        Collect a single training example.

        Returns:
            bool: True if example was accepted, False if filtered out
        """
        # Quality filter
        if quality_score < self.quality_threshold:
            logger.debug(f"Example filtered: quality {quality_score} < {self.quality_threshold}")
            return False

        # Create example
        example = TrainingExample(
            user_query=user_query,
            rag_context=rag_context,
            user_preferences=user_preferences,
            calculation_task=calculation_task,
            calculation_selection=calculation_selection,
            calculation_results=calculation_results,
            narrative_response=narrative_response,
            quality_score=quality_score,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id if not self.enable_privacy_filter else self._anonymize_user_id(user_id),
            session_id=session_id,
            user_feedback=user_feedback,
            user_rating=user_rating,
        )

        # Deduplication
        example_hash = example.get_hash()
        if example_hash in self.seen_hashes:
            logger.debug(f"Example filtered: duplicate (hash={example_hash})")
            return False

        self.seen_hashes.add(example_hash)

        # Privacy filter
        if self.enable_privacy_filter:
            example = self._apply_privacy_filter(example)

        # Add to batch
        self.current_batch.append(example)
        logger.info(f"Collected training example (quality={quality_score:.2f})")

        # Auto-persist on batch size
        if len(self.current_batch) >= self.batch_size:
            self.persist_batch()

        return True

    def persist_batch(self) -> int:
        """
        Persist current batch to disk.

        Returns:
            int: Number of examples persisted
        """
        if not self.current_batch:
            return 0

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = self.storage_path / f"batch_{timestamp}.jsonl"

        # Write JSONL format (one JSON per line)
        count = 0
        with open(filename, "w") as f:
            for example in self.current_batch:
                f.write(json.dumps(asdict(example)) + "\n")
                count += 1

        logger.info(f"Persisted {count} examples to {filename}")

        # Clear batch
        self.current_batch = []

        return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics"""
        # Count total examples across all batches
        total_examples = 0
        batch_files = list(self.storage_path.glob("batch_*.jsonl"))

        for batch_file in batch_files:
            with open(batch_file, "r") as f:
                total_examples += sum(1 for _ in f)

        # Quality score distribution
        quality_scores = []
        for batch_file in batch_files:
            with open(batch_file, "r") as f:
                for line in f:
                    example_data = json.loads(line)
                    quality_scores.append(example_data["quality_score"])

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        return {
            "total_examples": total_examples,
            "batch_files": len(batch_files),
            "current_batch_size": len(self.current_batch),
            "unique_hashes": len(self.seen_hashes),
            "average_quality_score": avg_quality,
            "storage_path": str(self.storage_path),
        }

    def export_for_finetuning(
        self,
        output_path: str,
        format: str = "gemini",
        min_quality: float = 0.9,
    ) -> int:
        """
        Export high-quality examples in fine-tuning format.

        Args:
            output_path: Where to save the export
            format: "gemini" or "openai"
            min_quality: Minimum quality score to include

        Returns:
            int: Number of examples exported
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        batch_files = list(self.storage_path.glob("batch_*.jsonl"))

        with open(output_file, "w") as out:
            for batch_file in batch_files:
                with open(batch_file, "r") as f:
                    for line in f:
                        example_data = json.loads(line)

                        # Quality filter
                        if example_data["quality_score"] < min_quality:
                            continue

                        # Reconstruct example
                        example = TrainingExample(**example_data)

                        # Convert to requested format
                        if format == "gemini":
                            formatted = example.to_gemini_format()
                        else:
                            raise ValueError(f"Unsupported format: {format}")

                        out.write(json.dumps(formatted) + "\n")
                        count += 1

        logger.info(f"Exported {count} examples to {output_file} (format={format})")
        return count

    def _anonymize_user_id(self, user_id: str) -> str:
        """Anonymize user ID for privacy"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    def _apply_privacy_filter(self, example: TrainingExample) -> TrainingExample:
        """Remove PII and sensitive data"""
        # Remove email addresses
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        example.user_query = re.sub(email_pattern, "[EMAIL]", example.user_query)
        example.narrative_response = re.sub(email_pattern, "[EMAIL]", example.narrative_response)

        # Remove phone numbers (simple pattern)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        example.user_query = re.sub(phone_pattern, "[PHONE]", example.user_query)
        example.narrative_response = re.sub(phone_pattern, "[PHONE]", example.narrative_response)

        # Remove specific dollar amounts over $1M (potentially sensitive)
        large_amount_pattern = r'\$[0-9]{1,3}(,[0-9]{3}){3,}'
        example.user_query = re.sub(large_amount_pattern, "$[LARGE_AMOUNT]", example.user_query)

        return example

    def __del__(self):
        """Ensure batch is persisted on cleanup"""
        if self.current_batch:
            self.persist_batch()
