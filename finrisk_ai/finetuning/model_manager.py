"""
Phase 5.3: Fine-Tuned Model Management

Manages fine-tuning jobs and fine-tuned Gemini models.

Features:
- Create fine-tuning jobs
- Monitor training progress
- Model versioning
- A/B testing support
- Rollback capabilities
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class FineTuningJob:
    """Represents a fine-tuning job"""

    job_id: str
    base_model: str
    train_dataset_path: str
    validation_dataset_path: Optional[str]
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    completed_at: Optional[str] = None
    tuned_model_name: Optional[str] = None
    error_message: Optional[str] = None

    # Training metrics
    epochs: int = 3
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None

    # Evaluation metrics
    final_loss: Optional[float] = None
    validation_loss: Optional[float] = None


@dataclass
class ModelVersion:
    """Represents a fine-tuned model version"""

    version_id: str
    model_name: str
    base_model: str
    created_at: str
    status: str  # "active", "deprecated", "archived"

    # Performance metrics
    benchmark_score: Optional[float] = None
    production_traffic_percentage: float = 0.0  # For A/B testing

    # Metadata
    training_examples_count: int = 0
    description: str = ""


class FineTunedModelManager:
    """
    Manages fine-tuned Gemini models.

    Features:
    - Create and monitor fine-tuning jobs
    - Version control for models
    - A/B testing support
    - Performance tracking
    - Rollback to previous versions
    """

    def __init__(
        self,
        gemini_api_key: str,
        models_registry_path: str = "data/models_registry.json",
    ):
        self.gemini_api_key = gemini_api_key
        self.models_registry_path = Path(models_registry_path)
        self.models_registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)

        # Load models registry
        self.models: Dict[str, ModelVersion] = self._load_registry()

        logger.info(f"FineTunedModelManager initialized with {len(self.models)} models")

    def create_finetuning_job(
        self,
        base_model: str,
        train_dataset_path: str,
        validation_dataset_path: Optional[str] = None,
        epochs: int = 3,
        learning_rate: Optional[float] = None,
        batch_size: Optional[int] = None,
    ) -> FineTuningJob:
        """
        Create a new fine-tuning job.

        Args:
            base_model: Base model to fine-tune (e.g., "gemini-1.5-flash")
            train_dataset_path: Path to training dataset (JSONL)
            validation_dataset_path: Path to validation dataset (JSONL)
            epochs: Number of training epochs
            learning_rate: Learning rate (None = auto)
            batch_size: Batch size (None = auto)

        Returns:
            FineTuningJob: Job information
        """
        logger.info(f"Creating fine-tuning job for {base_model}")

        # Validate dataset files exist
        if not Path(train_dataset_path).exists():
            raise FileNotFoundError(f"Training dataset not found: {train_dataset_path}")

        # NOTE: Gemini fine-tuning API is still in preview/limited access
        # This is a placeholder implementation for when it becomes available
        # For now, we simulate the job creation

        job_id = f"ft-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        job = FineTuningJob(
            job_id=job_id,
            base_model=base_model,
            train_dataset_path=train_dataset_path,
            validation_dataset_path=validation_dataset_path,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
            epochs=epochs,
            learning_rate=learning_rate,
            batch_size=batch_size,
        )

        # In production, this would call Gemini's fine-tuning API:
        # operation = genai.create_tuned_model(
        #     source_model=base_model,
        #     training_data=train_data,
        #     ...
        # )

        logger.info(f"Created fine-tuning job: {job_id}")
        logger.warning(
            "Note: Gemini fine-tuning API is in limited preview. "
            "This is a simulation. Check Google AI documentation for access."
        )

        return job

    def get_job_status(self, job_id: str) -> FineTuningJob:
        """
        Get status of a fine-tuning job.

        In production, this would poll the Gemini API for job status.
        """
        # Placeholder implementation
        logger.info(f"Checking status for job {job_id}")

        # In production:
        # operation = genai.get_tuned_model_operation(job_id)
        # return operation.status

        return FineTuningJob(
            job_id=job_id,
            base_model="gemini-1.5-flash",
            train_dataset_path="",
            validation_dataset_path=None,
            status="simulated",  # Would be "completed" in production
            created_at=datetime.utcnow().isoformat(),
        )

    def register_model(
        self,
        model_name: str,
        base_model: str,
        training_examples_count: int,
        description: str = "",
        benchmark_score: Optional[float] = None,
    ) -> ModelVersion:
        """
        Register a new fine-tuned model version.

        Args:
            model_name: Gemini tuned model name (e.g., "tunedModels/my-model-abc123")
            base_model: Base model used
            training_examples_count: Number of training examples
            description: Model description
            benchmark_score: Performance score

        Returns:
            ModelVersion: Registered model version
        """
        version_id = f"v{len(self.models) + 1}_{datetime.utcnow().strftime('%Y%m%d')}"

        model = ModelVersion(
            version_id=version_id,
            model_name=model_name,
            base_model=base_model,
            created_at=datetime.utcnow().isoformat(),
            status="active",
            benchmark_score=benchmark_score,
            production_traffic_percentage=0.0,  # Start with 0% traffic
            training_examples_count=training_examples_count,
            description=description,
        )

        self.models[version_id] = model
        self._save_registry()

        logger.info(f"Registered model: {version_id} ({model_name})")
        return model

    def set_traffic_split(self, version_id: str, traffic_percentage: float):
        """
        Set traffic percentage for A/B testing.

        Args:
            version_id: Model version ID
            traffic_percentage: Percentage of traffic (0.0-100.0)
        """
        if version_id not in self.models:
            raise ValueError(f"Model version not found: {version_id}")

        if not 0.0 <= traffic_percentage <= 100.0:
            raise ValueError("Traffic percentage must be between 0 and 100")

        self.models[version_id].production_traffic_percentage = traffic_percentage
        self._save_registry()

        logger.info(f"Set traffic for {version_id}: {traffic_percentage}%")

    def get_active_model(self, traffic_sample: float = None) -> Optional[ModelVersion]:
        """
        Get active model for serving requests.

        Uses traffic_sample (0.0-1.0) for A/B testing.
        """
        active_models = [m for m in self.models.values() if m.status == "active"]

        if not active_models:
            return None

        # If only one active model, return it
        if len(active_models) == 1:
            return active_models[0]

        # A/B testing: use traffic_sample to select model
        if traffic_sample is not None:
            cumulative = 0.0
            for model in active_models:
                cumulative += model.production_traffic_percentage / 100.0
                if traffic_sample <= cumulative:
                    return model

        # Default: return highest traffic model
        return max(active_models, key=lambda m: m.production_traffic_percentage)

    def deprecate_model(self, version_id: str):
        """Deprecate a model version (stops receiving traffic)"""
        if version_id not in self.models:
            raise ValueError(f"Model version not found: {version_id}")

        self.models[version_id].status = "deprecated"
        self.models[version_id].production_traffic_percentage = 0.0
        self._save_registry()

        logger.info(f"Deprecated model: {version_id}")

    def rollback_to_version(self, version_id: str):
        """
        Rollback to a previous model version.

        Sets specified version to 100% traffic, deprecates others.
        """
        if version_id not in self.models:
            raise ValueError(f"Model version not found: {version_id}")

        # Deprecate all other models
        for vid, model in self.models.items():
            if vid != version_id:
                model.status = "deprecated"
                model.production_traffic_percentage = 0.0

        # Activate rollback target
        self.models[version_id].status = "active"
        self.models[version_id].production_traffic_percentage = 100.0

        self._save_registry()

        logger.info(f"Rolled back to model version: {version_id}")

    def list_models(self) -> List[ModelVersion]:
        """List all model versions"""
        return list(self.models.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get model registry statistics"""
        models_list = list(self.models.values())

        return {
            "total_models": len(models_list),
            "active_models": len([m for m in models_list if m.status == "active"]),
            "deprecated_models": len([m for m in models_list if m.status == "deprecated"]),
            "total_traffic_allocated": sum(
                m.production_traffic_percentage for m in models_list if m.status == "active"
            ),
        }

    def _load_registry(self) -> Dict[str, ModelVersion]:
        """Load models registry from disk"""
        if not self.models_registry_path.exists():
            return {}

        with open(self.models_registry_path, "r") as f:
            data = json.load(f)

        models = {}
        for version_id, model_data in data.items():
            models[version_id] = ModelVersion(**model_data)

        return models

    def _save_registry(self):
        """Save models registry to disk"""
        data = {
            version_id: asdict(model)
            for version_id, model in self.models.items()
        }

        with open(self.models_registry_path, "w") as f:
            json.dump(data, f, indent=2)
