"""Training orchestration for Précis."""

import logging
from pathlib import Path
from typing import Optional

from transformers import (
    Trainer,
    TrainingArguments,
    PreTrainedModel,
    PreTrainedTokenizer,
    DataCollatorForLanguageModeling,
)
from torch.utils.data import Dataset

from src.config import TrainingConfig

logger = logging.getLogger(__name__)


class PrecisTrainer:
    """Wrapper around HuggingFace Trainer for summarization fine-tuning."""

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        config: Optional[TrainingConfig] = None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.config = config or TrainingConfig()
        
        self.training_args = self._create_training_args()
        self.trainer = self._create_trainer()

    def _create_training_args(self) -> TrainingArguments:
        """Create HuggingFace TrainingArguments from config."""
        return TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_ratio=self.config.warmup_ratio,
            weight_decay=self.config.weight_decay,
            max_grad_norm=self.config.max_grad_norm,
            optim=self.config.optim,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps if self.eval_dataset else None,
            evaluation_strategy="steps" if self.eval_dataset else "no",
            save_total_limit=3,
            load_best_model_at_end=bool(self.eval_dataset),
            seed=self.config.seed,
            fp16=True,
            report_to="none",
        )

    def _create_trainer(self) -> Trainer:
        """Create HuggingFace Trainer instance."""
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        return Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            data_collator=data_collator,
        )

    def train(self) -> None:
        """Execute training loop."""
        logger.info("Starting training...")
        self.trainer.train()
        logger.info("Training complete.")

    def evaluate(self) -> dict:
        """Run evaluation and return metrics."""
        if self.eval_dataset is None:
            logger.warning("No eval dataset provided")
            return {}
        
        logger.info("Running evaluation...")
        return self.trainer.evaluate()

    def save(self, output_path: Optional[str] = None) -> None:
        """Save model checkpoint."""
        path = output_path or self.config.output_dir
        Path(path).mkdir(parents=True, exist_ok=True)
        self.trainer.save_model(path)
        self.tokenizer.save_pretrained(path)
        logger.info(f"Model saved to {path}")
