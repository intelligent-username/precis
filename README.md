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



<h1 align="center">Précis</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python" alt="Python 3.11">
  <img src="https://img.shields.io/badge/node-18+-green?style=flat-square&logo=nodedotjs" alt="Node 18+">
  <img src="https://img.shields.io/badge/ollama-required-orange?style=flat-square&logo=ollama" alt="Ollama">
  <img src="https://img.shields.io/badge/license-GPL--3.0-brightgreen?style=flat-square" alt="License">
</p>

<p align="center">
  <em>Compress long-form content into clear, structured summaries.</em>
</p>

<p align="center">
  Paste a YouTube link, drop in an article, or upload a text file.<br>
  Précis extracts the key facts into a concise summary using a local LLM via <a href="https://ollama.com">Ollama</a>.
</p>

---

## Features

|           Capability      |                                  Description                                  |
|---------------------------|-------------------------------------------------------------------------------|
| **YouTube summarization** | Paste a URL; transcript is fetched automatically via `youtube-transcript-api` |
| **Article / transcript**  | Paste any text directly                                                       |
| **File upload**           | Drag-and-drop `.txt` files                                                    |
| **Streaming**             | Summaries stream token-by-token from Ollama via NDJSON                        |
| **Model switching**       | Choose between available Ollama models from the UI                            |

---

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

---

## Local Setup

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+ (or an equivalent alternative)
- **Ollama** (`ollama serve` to run)
- At least one model pulled, e.g. `ollama pull phi4-mini:latest`

---

### Run the Fine-Tuning

Scripts live in `scripts/`. The project has been tested primarily with **phi4-mini** (Microsoft) and **Qwen 3-4b** (Alibaba), but you can use whichever model you like.

```bash
ollama pull phi4-mini:latest
ollama pull qwen3:4b
```

---

### Test Fine-Tuning Quality

To evaluate summarization accuracy, run the script below against the `test` split. It uses **BERTScore** (0 to 1.0, higher is better), comparing semantic similarity between generated summaries and references. This captures key facts without penalizing different wording.

```bash
python -m scripts.test --model phi4-mini:latest
```

---

### Start the Backend

```bash
pip install -r ../requirements.txt
cd backend
uvicorn app:app --reload
```

Served at **`http://localhost:8000`** with interactive docs at `/docs`.

---

### Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Served at **`http://localhost:5173`**.

The frontend dev server proxies API calls to the backend automatically, so you only need to visit `http://localhost:5173`.

---

## Data

<!-- markdownlint-disable MD033 -->

References for datasets and papers used in this project. Click the arrow to expand BibTeX citations.

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

---

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

---

### SQuALITY (Long-Document QA)

~6,000 stories from Project Gutenberg with human-written summaries and QA pairs, designed to test long-document understanding.

Wang, A., Pang, R. Y., Chen, A., Phang, J., & Bowman, S. R. (2022). *SQuALITY: Building a Long-Document Summarization Dataset the Hard Way*. arXiv:2205.11465. [https://arxiv.org/abs/2205.11465](https://arxiv.org/abs/2205.11465) | [GitHub](https://github.com/nyu-mll/SQuALITY)

<details>
<summary>BibTeX</summary>

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

---

### MS MARCO (Concise QA)

Real user queries from Bing paired with relevant web passages. Useful for concise QA tasks.

Nguyen, T., Rosenberg, M., Song, X., Gao, J., Tiwary, S., Majumder, R., & Deng, L. (2016). *MS MARCO: A Human Generated Machine Reading Comprehension Dataset*.

<details>
<summary>BibTeX</summary>

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

---

### QMSum (Query-based Meeting Summarization)

Transcript QA dataset sourced from meetings. [GitHub](https://github.com/Yale-LILY/QMSum)

Zhong, M., Yin, D., Yu, T., Zaidi, A., Mutuma, M., Jha, R., Awadallah, A. H., Celikyilmaz, A., Liu, Y., Qiu, X., & Radev, D. (2021). *QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization*. NAACL 2021. [https://arxiv.org/abs/2104.05938](https://arxiv.org/abs/2104.05938)

<details>
<summary>BibTeX</summary>

```bibtex
@inproceedings{zhong2021qmsum,
   title={{QMS}um: {A} {N}ew {B}enchmark for {Q}uery-based {M}ulti-domain {M}eeting {S}ummarization},
   author={Zhong, Ming and Yin, Da and Yu, Tao and Zaidi, Ahmad and Mutuma, Mutethia and Jha, Rahul and Hassan Awadallah, Ahmed and Celikyilmaz, Asli and Liu, Yang and Qiu, Xipeng and Radev, Dragomir},
   booktitle={North American Association for Computational Linguistics (NAACL)},
   year={2021}
}
```

</details>

---

## License

[GPL-3.0](LICENSE.md)
