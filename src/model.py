"""Model loading utilities for Précis."""

import logging
from typing import Optional, Tuple

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizer,
)

from src.config import ModelConfig

logger = logging.getLogger(__name__)


def get_quantization_config(config: ModelConfig) -> Optional[BitsAndBytesConfig]:
    """Create BitsAndBytes quantization configuration."""
    if config.load_in_4bit:
        compute_dtype = getattr(torch, config.bnb_4bit_compute_dtype)
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_quant_type=config.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
        )
    elif config.load_in_8bit:
        return BitsAndBytesConfig(load_in_8bit=True)
    return None


def load_tokenizer(config: Optional[ModelConfig] = None) -> PreTrainedTokenizer:
    """Load and configure the tokenizer."""
    if config is None:
        config = ModelConfig()

    logger.info(f"Loading tokenizer: {config.model_id}")
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_id,
        trust_remote_code=config.trust_remote_code,
        cache_dir=config.cache_dir,
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "right"
    
    return tokenizer


def load_model(config: Optional[ModelConfig] = None) -> PreTrainedModel:
    """Load the base model with optional quantization."""
    if config is None:
        config = ModelConfig()

    logger.info(f"Loading model: {config.model_id}")
    quantization_config = get_quantization_config(config)

    model = AutoModelForCausalLM.from_pretrained(
        config.model_id,
        quantization_config=quantization_config,
        device_map=config.device_map,
        trust_remote_code=config.trust_remote_code,
        cache_dir=config.cache_dir,
        torch_dtype=torch.float16 if quantization_config else "auto",
    )
    
    logger.info(f"Model loaded. Parameters: {model.num_parameters():,}")
    return model


def prepare_for_training(model: PreTrainedModel, gradient_checkpointing: bool = True) -> PreTrainedModel:
    """Prepare model for training with gradient checkpointing and k-bit setup."""
    if gradient_checkpointing:
        model.gradient_checkpointing_enable()

    if getattr(model, "is_loaded_in_4bit", False) or getattr(model, "is_loaded_in_8bit", False):
        from peft import prepare_model_for_kbit_training
        model = prepare_model_for_kbit_training(model)

    return model


def load_model_and_tokenizer(config: Optional[ModelConfig] = None) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """Load both model and tokenizer."""
    if config is None:
        config = ModelConfig()
    return load_model(config), load_tokenizer(config)
