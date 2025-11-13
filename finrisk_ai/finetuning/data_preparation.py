"""
Phase 5.2: Fine-Tuning Data Preparation

Prepares collected training data for Gemini fine-tuning.

Steps:
1. Load and validate training examples
2. Split into train/validation sets
3. Format for Gemini API
4. Apply data augmentation (optional)
5. Create fine-tuning datasets
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DatasetSplit:
    """Train/validation split of fine-tuning data"""

    train_examples: List[Dict[str, Any]]
    validation_examples: List[Dict[str, Any]]
    train_path: str
    validation_path: str

    @property
    def train_size(self) -> int:
        return len(self.train_examples)

    @property
    def validation_size(self) -> int:
        return len(self.validation_examples)

    @property
    def total_size(self) -> int:
        return self.train_size + self.validation_size


class FineTuningDataPreparator:
    """
    Prepares training data for Gemini fine-tuning.

    Features:
    - Train/validation split
    - Data validation
    - Format conversion
    - Data augmentation
    - Quality metrics
    """

    def __init__(
        self,
        validation_split: float = 0.1,
        random_seed: int = 42,
        enable_augmentation: bool = False,
    ):
        self.validation_split = validation_split
        self.random_seed = random_seed
        self.enable_augmentation = enable_augmentation

        random.seed(random_seed)
        logger.info(f"FineTuningDataPreparator initialized (validation_split={validation_split})")

    def prepare_dataset(
        self,
        input_path: str,
        output_dir: str,
        min_examples: int = 100,
    ) -> DatasetSplit:
        """
        Prepare fine-tuning dataset from collected examples.

        Args:
            input_path: Path to exported training data (JSONL)
            output_dir: Where to save prepared datasets
            min_examples: Minimum number of examples required

        Returns:
            DatasetSplit: Train/validation split info
        """
        logger.info(f"Preparing dataset from {input_path}")

        # Load examples
        examples = self._load_examples(input_path)
        logger.info(f"Loaded {len(examples)} examples")

        # Validate
        if len(examples) < min_examples:
            raise ValueError(
                f"Insufficient training examples: {len(examples)} < {min_examples}. "
                f"Collect more production data before fine-tuning."
            )

        # Validate format
        examples = self._validate_examples(examples)
        logger.info(f"Validated {len(examples)} examples")

        # Apply augmentation
        if self.enable_augmentation:
            examples = self._augment_data(examples)
            logger.info(f"Augmented to {len(examples)} examples")

        # Split train/validation
        train_examples, val_examples = self._split_data(examples)
        logger.info(f"Split: {len(train_examples)} train, {len(val_examples)} validation")

        # Save datasets
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        train_path = output_path / "train.jsonl"
        val_path = output_path / "validation.jsonl"

        self._save_dataset(train_examples, train_path)
        self._save_dataset(val_examples, val_path)

        logger.info(f"Saved train dataset to {train_path}")
        logger.info(f"Saved validation dataset to {val_path}")

        return DatasetSplit(
            train_examples=train_examples,
            validation_examples=val_examples,
            train_path=str(train_path),
            validation_path=str(val_path),
        )

    def _load_examples(self, input_path: str) -> List[Dict[str, Any]]:
        """Load examples from JSONL file"""
        examples = []
        with open(input_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))
        return examples

    def _validate_examples(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate examples and filter out invalid ones.

        Checks:
        - Required fields present
        - Non-empty text_input and output
        - Reasonable length
        """
        valid_examples = []

        for i, example in enumerate(examples):
            # Check required fields
            if "text_input" not in example or "output" not in example:
                logger.warning(f"Example {i}: missing required fields")
                continue

            # Check non-empty
            if not example["text_input"].strip() or not example["output"].strip():
                logger.warning(f"Example {i}: empty input or output")
                continue

            # Check length (Gemini limits)
            if len(example["text_input"]) > 30000:  # Conservative limit
                logger.warning(f"Example {i}: input too long ({len(example['text_input'])} chars)")
                continue

            if len(example["output"]) > 10000:
                logger.warning(f"Example {i}: output too long ({len(example['output'])} chars)")
                continue

            valid_examples.append(example)

        removed_count = len(examples) - len(valid_examples)
        if removed_count > 0:
            logger.info(f"Filtered out {removed_count} invalid examples")

        return valid_examples

    def _split_data(
        self,
        examples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split data into train and validation sets"""
        # Shuffle for random split
        shuffled = examples.copy()
        random.shuffle(shuffled)

        # Calculate split point
        val_size = int(len(shuffled) * self.validation_split)
        train_size = len(shuffled) - val_size

        train_examples = shuffled[:train_size]
        val_examples = shuffled[train_size:]

        return train_examples, val_examples

    def _augment_data(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply data augmentation to increase training set size.

        Techniques:
        - Paraphrase user queries
        - Vary reporting style prompts
        - Inject synonyms
        """
        augmented = examples.copy()

        # Augmentation techniques (simplified)
        for example in examples[:]:  # Iterate over original examples
            # Technique 1: Vary prompt style
            if random.random() < 0.3:  # 30% augmentation rate
                augmented_example = example.copy()

                # Add variation to input
                original_input = example["text_input"]
                variation_prefix = random.choice([
                    "Please analyze: ",
                    "I need help with: ",
                    "Can you evaluate: ",
                    "Help me understand: ",
                ])

                # Inject variation (simplified - in production, use more sophisticated methods)
                if "USER QUERY:" in original_input:
                    augmented_example["text_input"] = original_input.replace(
                        "USER QUERY:",
                        f"USER QUERY: {variation_prefix}",
                        1
                    )
                    augmented.append(augmented_example)

        logger.info(f"Data augmentation: {len(examples)} -> {len(augmented)} examples")
        return augmented

    def _save_dataset(self, examples: List[Dict[str, Any]], output_path: Path):
        """Save dataset in JSONL format"""
        with open(output_path, "w") as f:
            for example in examples:
                f.write(json.dumps(example) + "\n")

    def analyze_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """
        Analyze dataset and return statistics.

        Returns metrics like:
        - Total examples
        - Average input/output length
        - Vocabulary size
        - Quality distribution
        """
        examples = self._load_examples(dataset_path)

        input_lengths = [len(ex["text_input"]) for ex in examples]
        output_lengths = [len(ex["output"]) for ex in examples]

        # Vocabulary analysis (simplified)
        all_text = " ".join([ex["text_input"] + " " + ex["output"] for ex in examples])
        vocab = set(all_text.lower().split())

        stats = {
            "total_examples": len(examples),
            "avg_input_length": sum(input_lengths) / len(input_lengths) if input_lengths else 0,
            "max_input_length": max(input_lengths) if input_lengths else 0,
            "avg_output_length": sum(output_lengths) / len(output_lengths) if output_lengths else 0,
            "max_output_length": max(output_lengths) if output_lengths else 0,
            "vocabulary_size": len(vocab),
        }

        return stats
