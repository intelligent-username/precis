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

All `/summarize/*` endpoints accept an optional `model` field to override the default and require `X-API-Key` header (`PRECIS_API_KEY`).

---

## Quick Start (Docker)

**One command** to build and run the whole stack (API + frontend + Ollama). This is the main way to run Précis — no manual `ollama serve`/`uvicorn`/`vite` needed.

> **Python runs inside the `precis` conda environment** — same as your local setup. The `Dockerfile` uses `continuumio/miniconda3` + `environment.yml` to create `conda env precis` (Python 3.11) and installs all deps there; the container's `PATH` points to `/opt/conda/envs/precis/bin`, so `uvicorn` runs from `precis`.

### 1. Prerequisites

- **Docker** + **Docker Compose** ([Install Docker Desktop](https://docs.docker.com/get-docker/))
- That's it. Python (via `precis` conda env), Node, and Ollama are all inside the containers. No local conda/Python/Node needed.

### 2. Configure

```bash
# from repo root
cp .env.example .env
# edit .env — set a strong secret:
# PRECIS_API_KEY=openssl rand -hex 32  (or any long random string)
# VITE_API_KEY must match PRECIS_API_KEY so the baked frontend can auth
```

> **`.env.example` defaults for Docker:**
> ```ini
> OLLAMA_BASE_URL=http://127.0.0.1:11434        # compose overrides to http://ollama:11434
> DEFAULT_MODEL=phi4-mini:latest
> AVAILABLE_MODELS=phi4-mini:latest
> PRECIS_API_KEY=replace-with-a-long-random-secret
> VITE_API_KEY=replace-with-a-long-random-secret
> PRECIS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000
> VITE_API_BASE_URL=                            # empty = same origin (correct for Docker)
> ```

Manually update `.env.example` to match the block above if your copy is older.

### 3. Run

```bash
docker compose up --watch
```

- First build takes ~4-6 min (multi-stage: Node build + `conda env create -f environment.yml` for `precis` — cached after first build).
- Opens: **http://localhost:5173** (Vite HMR) + API at **http://localhost:8000** (`/docs`, `/health`). With `--watch`, edits to `backend/` and `frontend/` hot-reload automatically.
- Compose healthchecks wait for Ollama (`/api/tags`) before starting the API (which runs as `conda run -n precis uvicorn`).

#### Pull a model (inside Ollama container)

The API will 503 until a model is installed. In a **second terminal**:

```bash
docker exec -it precis-ollama ollama pull phi4-mini:latest
# optional extras:
docker exec -it precis-ollama ollama pull llama3.1:latest
docker exec -it precis-ollama ollama pull qwen3:4b
docker exec -it precis-ollama ollama list
```

Then refresh http://localhost:5173 — the model selector populates automatically (`GET /models` proxied to `:8000`).

#### Useful commands

```bash
docker compose up --watch -d   # detached with watch
docker compose logs -f api     # tail API logs
docker compose logs -f ollama
docker compose logs -f frontend
docker compose down            # stop
docker compose down -v         # stop + wipe Ollama model cache (only if using named volume)
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/status
# prod without watch/HMR (static frontend at 8000):
docker compose -f docker-compose.yml up --build
```

#### Single-image run (without compose / without Ollama sidecar)

If you just want the API image and already run Ollama natively (`ollama serve` on host):

```bash
docker build -t precis .
docker run --rm -p 8000:8000 --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  precis
# Windows/Mac: host.docker.internal resolves to host. Linux: add --add-host=host.docker.internal:host-gateway
```

#### Hugging Face Spaces

`sdk: docker` with `EXPOSE 8000 7860` + `ENV PORT=8000` + `CMD sh -c "uvicorn ... --port ${PORT:-8000}"` means the same image works everywhere: locally `http://localhost:8000` (compose sets `PORT=8000`), on HF Spaces Hugging Face sets `PORT=7860` automatically and the container listens on `7860` with no extra config.

---

## Manual Development

Use this if you want hot-reload for the frontend/backend separately. Docker remains the reproducible path.

### Prerequisites

- **Conda** (Miniconda/Anaconda/Mamba) with env **`precis`** (`conda env create -f environment.yml` / `conda activate precis`) — Python 3.11, same env the Docker image uses
  - Alternative without conda: **Python** 3.11+ + `pip install -r requirements.txt`
- **Node.js** 18+
- **Ollama** (`ollama serve` to run) + at least one model: `ollama pull phi4-mini:latest`

### 1. Environment

```bash
cp .env.example .env
# set PRECIS_API_KEY, VITE_API_KEY (same value), and for local:
# OLLAMA_BASE_URL=http://127.0.0.1:11434
# VITE_API_BASE_URL=http://localhost:8000   # or leave empty and rely on Vite proxy
```

### 2. Run the Fine-Tuning (optional)

Scripts live in `scripts/`. Tested primarily with **phi4-mini** (Microsoft) and **Qwen 3-4b** (Alibaba).

```bash
ollama pull phi4-mini:latest
ollama pull llama3.1:latest
```

### 3. Test Fine-Tuning Quality

To evaluate summarization accuracy, run the script below against the `test` split. It uses **BERTScore** (0 to 1.0, higher is better), comparing semantic similarity between generated summaries and references.

```bash
python -m scripts.test --model phi4-mini:latest
```

### 4. Start the Backend

```bash
# With conda (recommended — mirrors Docker):
conda env create -f environment.yml   # once
conda activate precis
pip install -r requirements.txt       # keep in sync if you edit requirements.txt
uvicorn backend.app:app --reload --port 8000
# or: cd backend && uvicorn app:app --reload --port 8000

# Without conda:
# pip install -r requirements.txt
# uvicorn backend.app:app --reload --port 8000
```

Served at **`http://localhost:8000`** with interactive docs at `/docs`.

### 5. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Served at **`http://localhost:5173`**.

`vite.config.js` proxies `/health`, `/status`, `/models`, `/summarize`, `/warmup`, `/unload` to `http://localhost:8000` (via `.env` `API_BASE_URL`/`VITE_PROXY_TARGET`), so you only need to visit `http://localhost:5173` — no manual `VITE_API_BASE_URL` required. `docker compose up --watch` syncs edits automatically.

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
