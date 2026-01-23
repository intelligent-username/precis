"""LoRA/PEFT configuration and utilities."""

import logging
from pathlib import Path
from typing import Optional

from peft import LoraConfig, get_peft_model, PeftModel, TaskType
from transformers import PreTrainedModel

from src.config import TrainingConfig

logger = logging.getLogger(__name__)


def get_lora_config(config: Optional[TrainingConfig] = None) -> LoraConfig:
    """Create LoRA configuration for summarization task."""
    if config is None:
        config = TrainingConfig()

    return LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.lora_target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )


def apply_lora(model: PreTrainedModel, config: Optional[TrainingConfig] = None) -> PeftModel:
    """Apply LoRA adapters to model."""
    lora_config = get_lora_config(config)
    logger.info(f"Applying LoRA with r={lora_config.r}, alpha={lora_config.lora_alpha}")
    
    peft_model = get_peft_model(model, lora_config)
    peft_model.print_trainable_parameters()
    
    return peft_model


def merge_and_save(model: PeftModel, output_path: str, tokenizer=None) -> None:
    """Merge LoRA weights into base model and save."""
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Merging LoRA weights...")
    merged_model = model.merge_and_unload()
    
    logger.info(f"Saving merged model to {output_dir}")
    merged_model.save_pretrained(output_dir)
    
    if tokenizer:
        tokenizer.save_pretrained(output_dir)
