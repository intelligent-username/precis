# Précis

A system for compressing long-form content into clear, structured summaries.

Précis is designed for articles, papers, and video transcripts. The goal is to extract meaningful content rather than paraphrase main ideas.

## Model

Qwen-2.5-7B-Instruct with 4-bit quantization (BitsAndBytes NF4) for efficiency. Fine-tuned using LoRA for summarization.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Training (with dummy data)

```bash
# Dry run to validate pipeline
python scripts/train.py --dry-run

# Full training
python scripts/train.py --epochs 3 --batch-size 4
```

### Evaluation

```bash
python scripts/evaluate.py --checkpoint ./outputs
```

## API

### Running the API

```bash
python app.py
# or
uvicorn app:app --reload
```

### Endpoints

- `GET /` — API documentation page
- `GET /health` — Health check
- `GET /status` — Service status and model info
- `POST /summarize` — Summarize content from URL (currently returns dummy data)
