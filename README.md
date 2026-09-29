# MyHR-RAG

**Ask an HR-policy question. Get an answer grounded in your documents, with a citation.**

The assistant does not invent policy. It **searches** Qdrant, **re-ranks** with Jina, then **Gemini** writes from those chunks only.

| | |
|---|---|
| **Now (`basic-rag`)** | Ingest policies → hybrid search → re-rank → agent → cited answer (CLI + Streamlit) |
| **Next (`ai-security`)** | Model Armor, semantic cache, category filter, eval, Groq fallback |
| **Later (`deployment`)** | Docker, Cloud Run, Google OAuth, Secret Manager |

Repo: [murshedjamilalif/MyHR-RAG](https://github.com/murshedjamilalif/MyHR-RAG) · work on branch **`basic-rag`**

---

## Why this exists

HR policies live as files (leave, WFH, notice, maternity, …). People ask in plain language. A raw LLM will guess. This project **indexes** the files once, then at question time **retrieves** the right passages so the model can only speak from evidence.

```
You:  How many paid annual leave days do I get?
App:  search_hr_policy  →  12 candidates  →  top 5 after Jina
      Gemini writes from those 5 chunks  →  answer + [Source: leave_policy.txt]
```

---

## Architecture

Three layers. **Ingestion is offline and one-time.** Chat never uploads files; it only reads Qdrant.

<p align="center">
  <img src="Images/6.png" alt="Overall architecture: user access, Cloud Run app, GCS / Qdrant / Jina / Gemini" width="100%">
</p>

| Layer | What it is | On this branch |
|---|---|---|
| **1 · User access** | Browser → Google OAuth → email allow-list | Not yet (`deployment`) |
| **2 · App** | Streamlit + agent (+ later guardrails and cache) | Agent + **CLI** (`main.py`) + **Streamlit** (`app.py`) |
| **3 · Cloud** | GCS, Qdrant, Jina, Vertex Gemini, optional LangSmith | **Yes** — ingest + query |

Dashed orange on the diagram: **ingest** (the only writer to Qdrant). Solid arrows at runtime: **retrieve → rerank → generate**.

<details>
<summary>What each cloud service does</summary>

| Service | Job |
|---|---|
| **Cloud Storage** (`gs://myhr-rag`) | Raw files + processed JSON |
| **Qdrant Cloud** | Hybrid search: dense vectors + BM25 keywords |
| **Jina** | Embed at ingest; rerank at query time |
| **Vertex AI Gemini** | Write the answer (`temperature=0`) |
| **Groq** | Fallback LLM — `ai-security` |
| **LangSmith** | Traces / eval — optional |

Gemini **does not** read the bucket. It only sees retrieved chunk text.

</details>

---

## Ingestion (run once)

`ingest.py` is the **only** writer to Qdrant. Collections that already have points are skipped unless you pass `--force`.

<p align="center">
  <img src="Images/1.png" alt="Six-step data ingestion from local data/ to Qdrant" width="100%">
</p>

| # | Stage | Detail |
|---|---|---|
| 1 | Local `data/` | 10 HR `.txt` policies + 8 noise docs (pdf / docx / pptx / txt) |
| 2 | GCS **raw** | `raw/myhr-rag-data/` (HR) and `raw/other-data/` (noise) |
| 3 | GCS **processed** | Parse binaries **once** → one JSON per file (`text`, `policy_category`) |
| 4 | Chunk | **500** characters, **60** overlap (`splitter.py`) |
| 5 | Embed | Jina `jina-embeddings-v2-base-en` → **768-dim** vectors |
| 6 | Upsert | Hybrid dense + BM25 into **two** Qdrant collections |

| Collection | What is in it | Used by |
|---|---|---|
| `myhr-rag-data` | Clean HR only | The assistant |
| `hr_policies_noisy_data` | HR + noise mixed | Later retrieval tests |

Bucket **name** = project ID = `myhr-rag`. Bucket **region** is set only when you create it (`--location=us-central1`). That is not `.env` `LOCATION`.

```bash
# always from the repo root, not from myhr_rag/
python ingest.py              # skip collections that already have data
python ingest.py --force      # rebuild both
python ingest.py --hr-only
python ingest.py --noisy-only
python ingest.py --no-upload  # Qdrant only (GCS already uploaded)
```

---

## Query path (this branch)

No guardrails, no cache, no Groq. Agent + search + Gemini.

<p align="center">
  <img src="Images/2.png" alt="RAG query: agent, hybrid retrieve, Jina rerank, Gemini" width="100%">
</p>

1. You run **`python main.py`** (five demo HR questions) or **`streamlit run app.py`**.
2. The agent **always** calls `search_hr_policy` before answering.
3. Qdrant hybrid retrieve — **12** candidates (`RERANK_CANDIDATE_K`).
4. Jina `jina-reranker-v2-base-multilingual` — keep **5** (`TOP_K_RESULTS`).
5. Chunks formatted as `[Source: filename]` + text.
6. **Gemini 3.5 Flash** (`LOCATION=global`) writes from those chunks only.

Demo questions in `main.py` include annual leave, notice during probation, WFH, leave in notice, maternity leave.

---

## Roadmap diagrams (not on `basic-rag` yet)

<details>
<summary>Phase 2 — Secure query (`ai-security`)</summary>

<p align="center">
  <img src="Images/3.png" alt="Guardrails, semantic cache, LiteLLM routing" width="100%">
</p>

Input Model Armor → cache → agent (category filter + rerank + Gemini / Groq) → output Model Armor → cache store.

</details>

<details>
<summary>Evaluation — LLM-as-judge</summary>

<p align="center">
  <img src="Images/4.png" alt="LangSmith evaluation with Groq judge" width="100%">
</p>

Hand-written Q&A, same retrieval path, Groq scores **correctness** and **groundedness**.

</details>

<details>
<summary>Phase 3 — Deploy (`deployment`)</summary>

<p align="center">
  <img src="Images/5.png" alt="Cloud Run build and OAuth session" width="100%">
</p>

`gcloud run deploy --source .` → Artifact Registry → Cloud Run → secrets. Users: URL → Google login → allow-list → chat.

</details>

---

## Quick start

Need: a GCP project **`myhr-rag`** with billing, a GCS bucket, a **running** Qdrant Cloud cluster, a [Jina](https://jina.ai) key, and `gcloud` on your PATH.

```bash
git clone https://github.com/murshedjamilalif/MyHR-RAG.git
cd MyHR-RAG
git checkout basic-rag

cp .env.example .env          # fill in real keys — never commit .env
uv venv && uv pip install -r requirements.txt

gcloud config set project myhr-rag
gcloud auth application-default login
gcloud auth application-default set-quota-project myhr-rag
gcloud auth login
gcloud services enable aiplatform.googleapis.com storage.googleapis.com --project=myhr-rag

python ingest.py --force      # from repo root
python main.py
streamlit run app.py
```

### `.env` that must be right

| Variable | Meaning |
|---|---|
| `PROJECT_ID` | `myhr-rag` |
| `LOCATION` | **`global`** for `gemini-3.5-flash` (not `us-central1`) |
| `LLM_MODEL_NAME` | `gemini-3.5-flash` |
| `REGION` | `us-central1` — Cloud Run later; does not move the bucket |
| `GCS_BUCKET_NAME` | `myhr-rag` (name only) |
| `JINA_API_KEY` | Jina embeddings + reranker |
| `QDRANT_URL` | REST URL, usually `https://….cloud.qdrant.io:6333` |
| `QDRANT_API_KEY` | Qdrant API key |

LangSmith (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`) is optional.

Windows PATH, Git Bash vs PowerShell, ADC vs `gcloud auth login`: [commands/gcp-project.md](commands/gcp-project.md). Git commands: [commands/github.md](commands/github.md).

---

## If something breaks

| Symptom | Cause | What to do |
|---|---|---|
| `No module named 'myhr_rag'` | Ran `python ingest.py` **inside** `myhr_rag/` | `cd` to repo root |
| Qdrant `WinError 10054` / TLS closed | Cluster paused or bad URL/key | Wake cluster in [Qdrant Cloud](https://cloud.qdrant.io); check `.env` |
| Gemini **403** `SERVICE_DISABLED` | Vertex API off | `gcloud services enable aiplatform.googleapis.com --project=myhr-rag` |
| Gemini **404** `gemini-3.5-flash` in `us-central1` | That model is not in Iowa | `LOCATION=global` (or use `gemini-2.5-flash` in Iowa until 20 Oct 2026) |

---

## Code map

Read Python in number order: [myhr_rag/SEQUENCE.md](myhr_rag/SEQUENCE.md).

```
MyHR-RAG/
├── ingest.py                 # write Qdrant (run from here)
├── main.py                   # CLI demo
├── app.py                    # Streamlit chat UI
├── data/                     # HR policies + data/noise/
├── Images/                   # diagrams on this page
├── commands/                 # gcloud / git notes
└── myhr_rag/
    ├── 01  config.py
    ├── 02  prompts.py
    ├── 03  logging_config.py
    ├── 04  document_loader.py
    ├── 05  processor.py
    ├── 06  splitter.py
    ├── 07  embeddings.py
    ├── 08  vector_store.py
    ├── 09  ingestion.py
    ├── 10  reranker.py
    ├── 11  tools.py
    ├── 12  llm.py
    ├── 13  agent.py
    ├── 14  pipeline.py
    └── 15  tracing.py
```

**Stack:** Python 3.12 · uv · LangChain / LangGraph · Vertex AI Gemini 3.5 Flash · Cloud Storage · Qdrant Cloud · Jina · Streamlit · LangSmith (optional)
