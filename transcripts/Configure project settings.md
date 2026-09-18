# Configure project settings

Notes from the “configure the project” step: after the GCP project exists, set
the values the RAG pipeline needs — Cloud Storage, Qdrant, Jina, LangSmith —
then load them in `hr_assistant/config.py`.

Secrets stay in `.env`. Never paste API keys into commands or git.

This machine’s GCP project is `myhr-rag`. `GCS_BUCKET_NAME` is the **same
string** as the project ID: `myhr-rag` → bucket `gs://myhr-rag`. Bucket names
are still globally unique — if create fails, that ID is already taken worldwide.

---

## What we are configuring, and why

The pipeline is modular. Every module reads the same settings:

| Setting | Why |
|---|---|
| `PROJECT_ID`, `LOCATION` / `REGION` | Vertex AI Gemini and GCS must know **which** GCP project and region. |
| `GCS_BUCKET_NAME` | Ingest uploads local `data/` here. Code creates `raw/` and `processed/` — you do not mkdir those by hand. |
| `QDRANT_URL`, `QDRANT_API_KEY` | Vector store. Chunks are embedded and stored in Qdrant Cloud, not in the GCS bucket. |
| `QDRANT_COLLECTION_NAME` | Clean HR-policy vectors (`hr_policies`). |
| `QDRANT_NOISY_COLLECTION_NAME` | Mixed/noisy collection for a later phase (`hr_policies_noisy_demo`). Set it now so it is not forgotten. |
| `JINA_API_KEY` | Embeddings and the reranker (REST). Generous free-tier credits. |
| `LANGSMITH_API_KEY` + `LANGSMITH_TRACING` | Optional traces of the agent (what ran before/after each LLM step). |

Flow: **local files → GCS (raw, then processed JSON) → embeddings → Qdrant**.
Gemini answers from retrieved chunks. Jina reranks. LangSmith only observes.

---

## 1. Create the Cloud Storage bucket

`gcloud storage buckets create` needs a **`gs://` URL**, plus project and
location. This is wrong (missing `gs://`):

```text
gcloud storage buckets create rag-hr-assistant-demo-hr-buckets
```

Error looks like: *create only accepts bucket URLs, example: gs://…*

**Correct** (Git Bash or PowerShell). Pick a name that is free worldwide:

```powershell
# This project
$env:PROJECT_ID = "myhr-rag"
$env:REGION = "us-central1"
$env:GCS_BUCKET_NAME = "myhr-rag"

gcloud storage buckets create gs://$env:GCS_BUCKET_NAME `
  --project=$env:PROJECT_ID `
  --location=$env:REGION

gcloud storage buckets describe gs://$env:GCS_BUCKET_NAME --format="value(name,location)"
```

Git Bash:

```bash
PROJECT_ID=myhr-rag
REGION=us-central1
GCS_BUCKET_NAME=myhr-rag

gcloud storage buckets create gs://$GCS_BUCKET_NAME \
  --project=$PROJECT_ID \
  --location=$REGION
```

A bucket is object storage for the corpus. `ingest.py` fills it; you do not
upload files in the console.

**If the name is taken** (`The bucket name … is already shared by all users`):
GCS names are global. Prefer `myhr-rag` to match the project ID; only change
it if Google rejects the create.

**If a leftover bucket already exists** in Cloud Storage → Buckets: you can
delete it and recreate so you see the create step, or keep it if it is empty
and put that name in `.env`.

Confirm in the console: Cloud Storage → Buckets → your bucket, empty until
ingest. Folders `raw/` (pdf/docx/pptx/txt) and `processed/` (one JSON per
document) appear when code runs.

---

## 2. Qdrant Cloud (vector store)

Qdrant holds embeddings so the agent can search policy chunks.

1. Open [Qdrant Cloud](https://cloud.qdrant.io), start free, sign in (Google is fine).
2. Create a cluster: cloud **GCP** (same cloud as the rest of this project),
   region e.g. Iowa / `us-central1`, name e.g. `hr-rag` (no spaces).
3. Copy and store:
   - **API key** → `QDRANT_API_KEY`
   - **Endpoint URL** → `QDRANT_URL`

The URL is *where* Python sends vectors. The key authenticates those calls.
GCS only stores documents; Qdrant stores vectors.

---

## 3. Jina API key (embeddings + reranker)

[Jina](https://jina.ai): embeddings and the multilingual reranker.

1. Sign in (Google is fine).
2. Docs → Embeddings / Reranker → **Get API key**.
3. Copy the key once → `JINA_API_KEY`. Treat it as a secret.

Model **names** (not secrets) later go in `config.py` / `.env` defaults — copy
them from Jina’s embeddings and reranker lists if you switch models.

---

## 4. LangSmith (optional tracing)

LangSmith traces the agent: which tool ran, which chunks came back, what the
model saw.

1. Open [LangSmith](https://smith.langchain.com), sign in.
2. New project, e.g. `hr-rag-with-gcp`.
3. Trace an existing app → **Generate API key**.
4. Paste the snippet into `.env` (this project uses **uv** and `.env`):

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=hr-rag-with-gcp
```

`LANGSMITH_TRACING=true` turns tracing on. Skip this block if you do not want
traces; the RAG path still runs.

---

## 5. `.env`

```powershell
cp .env.example .env
```

Fill in (no quotes unless the value needs them):

```env
PROJECT_ID=myhr-rag
LOCATION=us-central1
GCS_BUCKET_NAME=myhr-rag

JINA_API_KEY=
QDRANT_URL=
QDRANT_API_KEY=

QDRANT_COLLECTION_NAME=hr_policies
QDRANT_NOISY_COLLECTION_NAME=hr_policies_noisy_demo

# optional
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=hr-rag-with-gcp
```

`config.py` loads this via `python-dotenv`. Nothing else has to “wire” `.env`.

You now have: **project**, **where files live (GCS)**, **how to embed/rerank
(Jina)**, **where vectors live (Qdrant)**, **optional traces (LangSmith)**.

---

## 6. `hr_assistant/config.py`

Create folder `hr_assistant` and file `config.py` (file **01** in the numbered
reading order). It is the single place for keys, URLs, model IDs, and sizes.
The rest of the pipeline imports from here instead of scattering `os.environ`.

| Block | What it holds |
|---|---|
| dotenv | Load `.env` so `os.getenv` works. |
| GCP | `PROJECT_ID`, `LOCATION`. |
| Secrets | `JINA_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`. |
| GCS paths | Bucket; `raw/` for HR policies vs other/noise; `processed/` JSON. Keep noise separate until a later stress-test phase merges them. |
| Qdrant collections | `hr_policies` and default `hr_policies_noisy_demo`. |
| LLM | Vertex **Gemini 2.5 Flash** (overridable from `.env`). |
| Jina models | Embedding model name and reranker (e.g. multilingual) from Jina’s docs. |
| Chunking | Chunk size **560**, plus overlap, for the splitter. |
| Retrieval | Retrieve a wide list (**12** = `RERANK_CANDIDATE_K`), rerank, keep top **5** (`TOP_K_RESULTS`). |
| LangSmith | Tracing flag/project. |
| `check_api_keys` | Fail fast if keys are missing before ingest or the agent runs. |

Raw vs processed: ingest reads mixed formats (pdf / docx / pptx / txt) into
GCS `raw/`, then writes one JSON per document under `processed/` before
chunk → embed → Qdrant.

Numbered files continue after config (`prompts`, `logging`, loaders, …). This
video stops at configuration; implementation of those modules is next.

---

## Checklist

- [ ] Bucket created with `gs://…` and a globally unique name
- [ ] Qdrant cluster on GCP; URL + API key in `.env`
- [ ] Jina API key in `.env`
- [ ] LangSmith key + tracing (optional)
- [ ] `.env` has `PROJECT_ID`, `LOCATION`, `GCS_BUCKET_NAME`, collection names
- [ ] `hr_assistant/config.py` reads `.env` and defines models, chunking, top-k

Next: modular pipeline under `hr_assistant/` (loaders, split, embed, ingest).
