#!/usr/bin/env python3
"""CLI training script for Précis."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.config import ModelConfig, TrainingConfig, DataConfig
    from src.model import load_model, load_tokenizer, prepare_for_training
    from src.tuning.lora import apply_lora
    from src.tuning.data import create_dummy_data, prepare_dataset
    from src.tuning.trainer import PrecisTrainer
except ImportError:
    from init.config import ModelConfig, TrainingConfig, DataConfig
    from init.model import load_model, load_tokenizer, prepare_for_training
    from init.tuning.lora import apply_lora
    from init.tuning.data import create_dummy_data, prepare_dataset
    from init.tuning.trainer import PrecisTrainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Train Précis summarization model")
    parser.add_argument("--model-id", type=str, default=None, help="HuggingFace model ID")
    parser.add_argument("--output-dir", type=str, default="./outputs", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--dry-run", action="store_true", help="Validate pipeline without training")
    parser.add_argument("--dummy-samples", type=int, default=100, help="Number of dummy samples")
    return parser.parse_args()


def main():
    args = parse_args()

    # Build configs
    model_config = ModelConfig()
    if args.model_id:
        model_config.model_id = args.model_id

    training_config = TrainingConfig(
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        lora_r=args.lora_r,
    )
    data_config = DataConfig()

    if args.dry_run:
        logger.info("=== DRY RUN MODE ===")
        logger.info(f"Model: {model_config.model_id}")
        logger.info(f"Output: {training_config.output_dir}")
        logger.info(f"Epochs: {training_config.num_epochs}, Batch: {training_config.batch_size}")
        logger.info(f"LoRA r: {training_config.lora_r}, alpha: {training_config.lora_alpha}")
        
        # Test data pipeline only
        dummy_data = create_dummy_data(5)
        logger.info(f"Dummy data sample: {dummy_data[0]}")
        logger.info("Dry run complete. Pipeline validated.")
        return

    # Load model and tokenizer
    logger.info("Loading model and tokenizer...")
    tokenizer = load_tokenizer(model_config)
    model = load_model(model_config)
    model = prepare_for_training(model)
    model = apply_lora(model, training_config)

    # Prepare data
    logger.info("Preparing training data...")
    train_data = create_dummy_data(args.dummy_samples)
    train_dataset = prepare_dataset(train_data, tokenizer, data_config)

    # Train
    trainer = PrecisTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        config=training_config,
    )
    trainer.train()
    trainer.save()

    logger.info("Training complete!")


if __name__ == "__main__":
    main()
