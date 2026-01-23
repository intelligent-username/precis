"""Data preparation utilities for training."""

import logging
from typing import Dict, List, Optional, Any

from torch.utils.data import Dataset
from transformers import PreTrainedTokenizer

from src.config import DataConfig

logger = logging.getLogger(__name__)


class SummarizationDataset(Dataset):
    """PyTorch Dataset for summarization training."""

    def __init__(
        self,
        data: List[Dict[str, str]],
        tokenizer: PreTrainedTokenizer,
        config: Optional[DataConfig] = None,
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.config = config or DataConfig()

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.data[idx]
        prompt = self.config.format_prompt(item[self.config.input_column])
        full_text = prompt + item[self.config.target_column] + self.tokenizer.eos_token

        encoding = self.tokenizer(
            full_text,
            truncation=True,
            max_length=self.config.max_input_length + self.config.max_target_length,
            padding="max_length",
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze(),
        }


def create_dummy_data(num_samples: int = 10) -> List[Dict[str, str]]:
    """Generate dummy data for testing the training pipeline."""
    samples = []
    for i in range(num_samples):
        samples.append({
            "text": f"This is sample document {i}. It contains information about topic {i % 3}. "
                    f"The document discusses various aspects and provides detailed analysis. "
                    f"Key points include methodology, results, and conclusions for study {i}.",
            "summary": f"Document {i} analyzes topic {i % 3}, covering methodology, results, and conclusions.",
        })
    logger.info(f"Created {num_samples} dummy samples")
    return samples


def prepare_dataset(
    data: List[Dict[str, str]],
    tokenizer: PreTrainedTokenizer,
    config: Optional[DataConfig] = None,
) -> SummarizationDataset:
    """Prepare dataset for training."""
    return SummarizationDataset(data, tokenizer, config)
