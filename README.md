# Précis

A system for compressing long-form content into clear, structured summaries. Précis is designed for videos, articles, and papers. Paste a YouTube link, drop in an article, or upload a text file. Précis will pulls the key facts into a single sentence using a local LLM via [Ollama](https://ollama.com).

## Features

- **YouTube summarization**: paste a URL, transcript is fetched automatically via `youtube-transcript-api`
- **Article / transcript**: paste any text directly
- **File upload**: drag-and-drop `.txt` files
- **Streaming**: summaries stream token-by-token from Ollama via NDJSON
- **Model switching**: choose between available Ollama models from the UI

## API Endpoints

| Method  |       Path              |     Description       |
|---------|-------------------------|-----------------------|
| `GET`   | `/health`               | Health check          |
| `GET`   | `/status`               | Ollama statuses, etc. |
| `GET`   | `/models`               | List available models |
| `POST`  | `/summarize/transcript` | Raw text summary      |
| `POST`  | `/summarize/youtube`    | YouTube video by URL  |
| `POST`  | `/summarize/file`       | `.txt` file summary   |

All `/summarize/*` endpoints accept an optional `model` field to override the default.

## Local Setup

### Prerequisites

- Python 3.11+,
- Node.js 18+ (or an alternative like [Bun](https://bun.sh)),
- [Ollama](https://ollama.com) installed and running (`ollama serve` is the command, although it may be on auto-start).
- At least one model pulled: `ollama pull phi4-mini:latest` (for example)

### Run the Fine-Tuning

Follow the scripts in `scripts/`, using any model you prefer. This project has been primarily tested with phi4-mini (from Microsoft) and Qwen 3-4b (from Alibaba) (`ollama pull qwen3:4b` to pull it).

### Start the Backend

```bash
# Create a venv or conda environment or whatever else you may want
pip install -r ../requirements.txt
cd backend
uvicorn app:app --reload
```

Runs on `http://localhost:8000`. Interactive docs at `/docs`.

### Run the Frontend

```bash
cd frontend
npm install   # or whatever replacement for npm you may be using
npm run dev
```

Runs on `http://localhost:5173`.

<!-- ## Data -->

<!-- Later, for fine-tuning data details -->

<!-- Interview Dataset -->
<!-- 

@article{zhu2021mediasum,
  title={MediaSum: A Large-scale Media Interview Dataset for Dialogue Summarization},
  author={Zhu, Chenguang and Liu, Yang and Mei, Jie and Zeng, Michael},
  journal={arXiv preprint arXiv:2103.06410},
  year={2021}
} 

-->

<!--------------------------------------------------------------------------------------------------->

<!-- 

@inproceedings{chen-etal-2021-dialogsum,
    title = "{D}ialog{S}um: {A} Real-Life Scenario Dialogue Summarization Dataset",
    author = "Chen, Yulong  and
      Liu, Yang  and
      Chen, Liang  and
      Zhang, Yue",
    booktitle = "Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021",
    month = aug,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.findings-acl.449",
    doi = "10.18653/v1/2021.findings-acl.449",
    pages = "5062--5074",
}

-->

<!------------------------------------------------------------------------------------------------->

<!-- "Single question followed by an answer" dataset -->

<!--

@article{wang2022squality,
  title        = {SQuALITY: Building a Long-Document Summarization Dataset the Hard Way},
  author       = {Wang, Alex and Pang, Richard Yuanzhe and Chen, Angelica and Phang, Jason and Bowman, Samuel R.},
  journal      = {arXiv preprint arXiv:2205.11465},
  year         = {2022},
  archivePrefix = {arXiv},
  eprint       = {2205.11465},
  primaryClass = {cs.CL},
  doi          = {10.48550/arXiv.2205.11465},
  url          = {https://doi.org/10.48550/arXiv.2205.11465}
}

-->

<!------------------------------------------------------------------------------------------------->

<!-- High Quality Query-Answer (concise) examples -->

<!--

@inproceedings{nguyen2016msmarco,
  title     = {MS MARCO: A Human Generated Machine Reading Comprehension Dataset},
  author    = {Nguyen, Tri and Rosenberg, Mir and Song, Xia and Gao, Jianfeng and Tiwary, Saurabh and Majumder, Rangan and Deng, Li},
  booktitle = {Proceedings of the Workshop on Cognitive Computation: Integrating Neural and Symbolic Approaches 2016},
  year      = {2016},
  publisher = {CEUR-WS.org}
}

-->

## License

[GPL-3.0](LICENSE.md)
