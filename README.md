---
title: Précis
emoji: 📝
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "1"
python_version: "3.11"
app_file: app.py
pinned: false
---
<!-- markdownlint-disable MD025 -->

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

Follow the scripts in `scripts/`, using any model you prefer. This project has been primarily tested with phi4-mini (from Microsoft) and Qwen 3-4b (from Alibaba).

You can pull the raw models with:

```bash
ollama pull phi4-mini:latest
ollama pull qwen3:4b
# And any other models you may want
```

<!-- 
You can also just download the fine-tuned versions right away from HuggingFace by running the following script, which downloads the fine-tuned models from my HuggingFace space:

```bash

```
 -->

### Test the Quality of the Fine-Tuning

Run the following script on the `test` split in order to get a sense of how accurately the model is summarizing the context. The script will use the BERTScore metric (which compares the sentiment of the generated summary with the sentiment of the reference summary) to give you a score out of 1.0, where higher is better. BERT is the most appropriate metric for this task since we want to ensure that the generated summary captures the same key facts as the reference summary, without penalizing different wording.

```bash
# Make sure you have the appropriate libraries installed (see requirements.txt and the instructions for running the backend).
python -m scripts.test --model phi4-mini:latest
```

### Start the Backend

```bash
# Create a venv or conda environment or whatever else you may want
pip install -r ../requirements.txt
cd backend
uvicorn app:app --reload
```

Runs on `http://localhost:8000`. Interactive docs at `/docs`.

### Run the Frontend

In another terminal, run:

```bash
cd frontend
npm install   # or use any npm alternative
npm run dev
```

Runs on `http://localhost:5173`.

**Development Setup**: The frontend dev server will automatically proxy API calls to the backend. Just access the app at `http://localhost:5173` during development.

## Data

<!-- markdownlint-disable MD033 -->

References for datasets/papers used in this project (with BibTeX available if you need to cite them formally).

### MediaSum (Interview Summarization)

Zhu, C., Liu, Y., Mei, J., & Zeng, M. (2021). *MediaSum: A Large-scale Media Interview Dataset for Dialogue Summarization*. arXiv:2103.06410. [https://arxiv.org/abs/2103.06410](https://arxiv.org/abs/2103.06410)

<details>
<summary>BibTeX</summary>

```bibtex
@article{zhu2021mediasum,
  title   = {MediaSum: A Large-scale Media Interview Dataset for Dialogue Summarization},
  author  = {Zhu, Chenguang and Liu, Yang and Mei, Jie and Zeng, Michael},
  journal = {arXiv preprint arXiv:2103.06410},
  year    = {2021}
}
```

</details>

### DialogSum (Dialogue Summarization)

Chen, Y., Liu, Y., Chen, L., & Zhang, Y. (2021). *DialogSum: A Real-Life Scenario Dialogue Summarization Dataset*. Findings of ACL-IJCNLP 2021. [https://aclanthology.org/2021.findings-acl.449](https://aclanthology.org/2021.findings-acl.449)

<details>

<summary>BibTeX</summary>

```bibtex
@inproceedings{chen-etal-2021-dialogsum,
  title     = {{D}ialog{S}um: {A} Real-Life Scenario Dialogue Summarization Dataset},
  author    = {Chen, Yulong and Liu, Yang and Chen, Liang and Zhang, Yue},
  booktitle = {Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021},
  month     = aug,
  year      = {2021},
  address   = {Online},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2021.findings-acl.449},
  doi       = {10.18653/v1/2021.findings-acl.449},
  pages     = {5062--5074}
}
```

</details>

### SQuALITY (Long-Document QA)

This dataset contains around 6000 stories ("long documents") from Project Gutenberg, along with human-written summaries and question-answer pairs. The dataset is designed to test the ability of models to understand and summarize long-form content. GitHub repo: [https://github.com/nyu-mll/SQuALITY](https://github.com/nyu-mll/SQuALITY)

Wang, A., Pang, R. Y., Chen, A., Phang, J., & Bowman, S. R. (2022). *SQuALITY: Building a Long-Document Summarization Dataset the Hard Way*. arXiv:2205.11465. [https://arxiv.org/abs/2205.11465](https://arxiv.org/abs/2205.11465)

<details> <summary>BibTeX</summary>

```bibtex
@article{wang2022squality,
  title         = {SQuALITY: Building a Long-Document Summarization Dataset the Hard Way},
  author        = {Wang, Alex and Pang, Richard Yuanzhe and Chen, Angelica and Phang, Jason and Bowman, Samuel R.},
  journal       = {arXiv preprint arXiv:2205.11465},
  year          = {2022},
  archivePrefix = {arXiv},
  eprint        = {2205.11465},
  primaryClass  = {cs.CL},
  doi           = {10.48550/arXiv.2205.11465},
  url           = {https://doi.org/10.48550/arXiv.2205.11465}
}
```

</details>

### MS MARCO (Concise QA)

This is a massive dataset of real user queries from Bing, along with passages from web documents that are relevant to those queries.

Nguyen, T., Rosenberg, M., Song, X., Gao, J., Tiwary, S., Majumder, R., & Deng, L. (2016). *MS MARCO: A Human Generated Machine Reading Comprehension Dataset*.

<details><summary>BibTeX</summary>

```bibtex
@inproceedings{nguyen2016msmarco,
  title     = {MS MARCO: A Human Generated Machine Reading Comprehension Dataset},
  author    = {Nguyen, Tri and Rosenberg, Mir and Song, Xia and Gao, Jianfeng and Tiwary, Saurabh and Majumder, Rangan and Deng, Li},
  booktitle = {Proceedings of the Workshop on Cognitive Computation: Integrating Neural and Symbolic Approaches 2016},
  year      = {2016},
  publisher = {CEUR-WS.org}
}
```

</details>

### QMSum

This dataset is for specifically taking in transcripts and answering questions about them. The GitHub repo for the dataset [and other details is here](https://github.com/Yale-LILY/QMSum).

Zhong, M., Yin, D., Yu, T., Zaidi, A., Mutuma, M., Jha, R., Awadallah, A. H., Celikyilmaz, A., Liu, Y., Qiu, X., & Radev, D. (2021). *QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization*. NAACL 2021. [https://arxiv.org/abs/2104.05938](https://arxiv.org/abs/2104.05938)

<details><summary>BibTeX</summary>

```bibtex
@inproceedings{zhong2021qmsum,
   title={{QMS}um: {A} {N}ew {B}enchmark for {Q}uery-based {M}ulti-domain {M}eeting {S}ummarization},
   author={Zhong, Ming and Yin, Da and Yu, Tao and Zaidi, Ahmad and Mutuma, Mutethia and Jha, Rahul and Hassan Awadallah, Ahmed and Celikyilmaz, Asli and Liu, Yang and Qiu, Xipeng and Radev, Dragomir},
   booktitle={North American Association for Computational Linguistics (NAACL)},
   year={2021}
}
```

</details>

## License

[GPL-3.0](LICENSE.md)
