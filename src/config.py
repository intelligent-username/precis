"""Configuration management for Précis."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ModelConfig:
    """Configuration for model loading and quantization."""
    model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    device_map: str = "auto"
    trust_remote_code: bool = True
    cache_dir: Optional[str] = None

    def __post_init__(self):
        if self.load_in_4bit and self.load_in_8bit:
            raise ValueError("Cannot enable both 4-bit and 8-bit quantization")


@dataclass
class TrainingConfig:
    """Configuration for LoRA fine-tuning."""
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    warmup_ratio: float = 0.03
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    max_seq_length: int = 2048
    optim: str = "paged_adamw_32bit"
    save_steps: int = 100
    logging_steps: int = 10
    eval_steps: int = 100
    output_dir: str = "./outputs"
    seed: int = 42


@dataclass
class DataConfig:
    """Configuration for dataset loading and preprocessing."""
    train_file: Optional[str] = None
    eval_file: Optional[str] = None
    input_column: str = "text"
    target_column: str = "summary"
    max_input_length: int = 1536
    max_target_length: int = 512
    train_split: float = 0.9
    prompt_template: str = (
        "Summarize the following document:\n\n"
        "### Document:\n{input}\n\n"
        "### Summary:\n"
    )

    def format_prompt(self, text: str) -> str:
        return self.prompt_template.format(input=text)
