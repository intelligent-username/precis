#!/usr/bin/env python3
"""CLI evaluation script for Précis."""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ModelConfig, DataConfig
from src.model import load_tokenizer
from src.tuning.data import create_dummy_data

from transformers import AutoModelForCausalLM
from peft import PeftModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Précis model")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to evaluate")
    parser.add_argument("--max-new-tokens", type=int, default=256, help="Max tokens to generate")
    return parser.parse_args()


def main():
    args = parse_args()
    config = ModelConfig()
    data_config = DataConfig()

    logger.info(f"Loading checkpoint from {args.checkpoint}")
    tokenizer = load_tokenizer(config)
    
    model = AutoModelForCausalLM.from_pretrained(
        args.checkpoint,
        device_map="auto",
        trust_remote_code=True,
    )

    # Generate on dummy samples
    samples = create_dummy_data(args.num_samples)
    
    for i, sample in enumerate(samples):
        prompt = data_config.format_prompt(sample["text"])
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        outputs = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.pad_token_id,
        )
        
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        summary = generated[len(prompt):]
        
        logger.info(f"\n=== Sample {i+1} ===")
        logger.info(f"Input: {sample['text'][:100]}...")
        logger.info(f"Generated: {summary}")
        logger.info(f"Reference: {sample['summary']}")


if __name__ == "__main__":
    main()
