# HR Policy Assistant — Basic RAG

> **This is the `basic-rag` branch — stage 1 of 3.**
> A plain, working RAG agent: ingestion, hybrid search, re-ranking, an
> agent with memory, a CLI and a Streamlit UI, LangGraph Studio. No
> guardrails, no evaluation, no deployment — those come next.
>
> | Branch | Adds |
> |---|---|
> | **`basic-rag`** *(here)* | the RAG pipeline end to end |
> | `security` | safety guardrails, scope filter, semantic cache, evaluation, red-team, LLM fallback |
> | `deployment` | Docker, Cloud Run, Google OAuth |

A RAG agent that answers HR-policy questions from real policy documents —
retrieval, metadata plumbing, hybrid (dense + BM25) search, and Jina
re-ranking for grounded, cited answers. The model is Vertex AI Gemini.

## Quick start

```bash
cp .env.example .env          # then fill in the values (see below)
uv venv                       # creates .venv (Python 3.12)
uv pip install -r requirements.txt

# gcloud — see “Point gcloud at the GCP project” below for why
gcloud --version
gcloud config set project myhr-rag
gcloud auth application-default login
gcloud auth application-default set-quota-project myhr-rag

uv run python ingest.py       # local data/ -> GCS -> Qdrant (run once)
uv run python main.py         # CLI demo
uv run streamlit run app.py   # chat UI
```

`.env` needs: `PROJECT_ID`, `LOCATION`, `GCS_BUCKET_NAME`, `JINA_API_KEY`,
`QDRANT_URL`, `QDRANT_API_KEY`. `LANGSMITH_API_KEY` + `LANGSMITH_TRACING=true`
are optional (request tracing).

Full GCP provisioning (project, billing, APIs, bucket) is in
[commands/commands-basic-rag.md](commands/commands-basic-rag.md).

---

## Local setup (Windows)

Python packages go in the project venv. `gcloud` does **not**.

| Tool | What it is | Where it lives |
|---|---|---|
| **uv** | Python package/venv manager | system PATH |
| **`.venv`** | Project Python environment (`(MyHR)` prompt) | `D:\CODE\AI\Projects\MyHR\.venv` |
| **`gcloud`** | Google Cloud CLI (auth, project, buckets) | Windows install, **not** the venv |

`requirements.txt` installs Python clients such as `google-cloud-storage`.
Those are what the app imports. `gcloud config`, `gcloud auth`, and
`gcloud storage` are shell commands — same idea as `git` or `uv`.

### 1. uv + Python venv

```powershell
uv --version
uv python install 3.12
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

Activate in **Command Prompt** with `.venv\Scripts\activate.bat`.
Activate in **PowerShell** with `.venv\Scripts\activate`.

After that the prompt shows `(MyHR)`. Run app code with `uv run …` (no
need to activate) or with `python` / `streamlit` after activating.

### 2. Install the Google Cloud CLI

`gcloud` is a Windows program. Do **not** try to put it inside `.venv`.

```powershell
winget install Google.CloudSDK
```

If winget says the package is already installed (and may ask for
`--include-unknown` to upgrade), that is fine — the CLI is already on
disk. It still has to be on **PATH** or `gcloud` will fail:

```
'gcloud' is not recognized as an internal or external command
```

Typical install location:

`C:\Users\USER\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin`

Confirm it with the full path:

```bat
"%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" --version
```

### 3. Put `gcloud` on PATH

Use the syntax for **this** terminal. `$env:Path` is PowerShell only.
In Command Prompt it is treated as a filename and you get
`The filename, directory name, or volume label syntax is incorrect.`

**Command Prompt (this session only):**

```bat
set PATH=%PATH%;%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin
gcloud --version
```

**PowerShell (this session only):**

```powershell
$env:Path += ";$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
gcloud --version
```

**Permanent (User PATH)** — then close the terminal and open a new one:

```powershell
$gcloudBin = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*google-cloud-sdk\bin*") {
  [Environment]::SetEnvironmentVariable("Path", "$userPath;$gcloudBin", "User")
}
```

Or skip PATH and call `gcloud` by full path every time:

```bat
"%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" config set project myhr-rag
```

### 4. Point gcloud at the GCP project

This app talks to **Vertex AI (Gemini)** and **Cloud Storage** from Python
(`google-cloud-storage`, `langchain-google-genai`). Those libraries do not
use your gcloud login by magic — they look for **Application Default
Credentials (ADC)** on disk. The commands below (1) pick the GCP project
and (2) write those credentials so ingest and the agent can call Google
APIs as you.

Replace `myhr-rag` if your project ID is different.

**Check the CLI is on PATH** — proves `gcloud` itself works (SDK 584+ is
fine). This does not log you in.

```powershell
gcloud --version
```

Expected: `Google Cloud SDK …`, plus `bq`, `core`, `gsutil`.

**Set the default project** — every later `gcloud` command, and the quota
project attached to ADC, targets this ID. Without it, calls go to the
wrong project or fail with “no project”.

```powershell
gcloud config set project myhr-rag
```

Expected: `Updated property [core/project].`

**Application Default Credentials** — opens a browser OAuth flow. On
success, credentials are saved to
`%APPDATA%\gcloud\application_default_credentials.json`. **Python**
(ingest, Streamlit, the agent) uses this file, not the `(MyHR)` venv.
This is different from `gcloud auth login`, which only authenticates the
**gcloud CLI** for commands you type. This project needs ADC because
Vertex AI and Cloud Storage are called from Python.

```powershell
gcloud auth application-default login
```

Expected: browser sign-in, then `Credentials saved to file: […\application_default_credentials.json]`.
Quota project `myhr-rag` may already be attached if the default project
was set first.

**Pin the quota / billing project on ADC** — client libraries send this
project for **quota and billing**. Vertex AI and GCS need it even when
ADC already exists; some APIs still fail without it.

```powershell
gcloud auth application-default set-quota-project myhr-rag
```

Expected: credentials saved again, and
`Quota project "myhr-rag" was added to ADC…`

**Log the gcloud CLI in** — ADC (above) is for Python. `gcloud billing`,
`gcloud services enable`, and `gcloud storage` use a **separate** CLI
login. Without it you get:

`You do not currently have an active account selected.`

```powershell
gcloud auth login
```

Expected: browser sign-in, then `You are now logged in as [you@gmail.com]`
and `Your current project is [myhr-rag]`.

**Do not run `gcloud config set account ACCOUNT`.** `ACCOUNT` in Google’s
error text is a **placeholder**. Pasting it sets the active account to the
literal string `ACCOUNT`, which has no credentials:

`Your current active account [ACCOUNT] does not have any valid credentials`

Switch back to the email from `gcloud auth login` (not the word ACCOUNT):

```powershell
gcloud config set account murshedjamilalif@gmail.com
```

Expected: `Updated property [core/account].`

**List billing accounts** — Vertex AI and Cloud Storage are not free at
scale; a GCP project must be **linked** to an open billing account or
API calls fail. This command is how you get the `ACCOUNT_ID` for
`gcloud billing projects link`. It does not charge anything by itself.

```powershell
gcloud billing accounts list
```

Expected (this machine):

```
ACCOUNT_ID            NAME                OPEN  MASTER_ACCOUNT_ID
01C1BA-71A95A-C16402  My Billing Account  True
```

- `ACCOUNT_ID` (`01C1BA-71A95A-C16402`) — pass this as
  `$BILLING_ACCOUNT_ID` when linking the project.
- `OPEN` must be `True` or the link will fail.
- `MASTER_ACCOUNT_ID` empty is normal for a standalone account.

Or run `gcloud auth login` again if the wrong account is still selected.
Check with `gcloud auth list` — the active account has a `*`.

---

## The code, in reading order

Every file is numbered in its docstring. `hr_assistant/`: **01** config ·
**02** prompts · **03** logging · **04** document_loader · **05** processor ·
**06** splitter · **07** embeddings · **08** vector_store · **09** ingestion ·
**10** reranker · **11** tools · **12** llm · **13** agent · **14** pipeline ·
**15** tracing. Entry scripts: **16** `ingest.py` · **17** `main.py` ·
**18** `app.py` · **19** `studio_graph.py`.

## The scripts

| Command | What it does |
|---|---|
| `uv run python ingest.py` | Ingest the corpus: local `data/` → GCS raw → GCS processed (pdf/docx/pptx parsed once) → Qdrant. Builds **both** collections. `--force` to rebuild, `--hr-only` / `--noisy-only` to limit scope. |
| `uv run python main.py` | CLI demo — a few questions through the agent. Bootstraps ingestion on first run if needed. |
| `uv run streamlit run app.py` | The chat UI. One conversation thread per browser session. |
| `uv run python -m hr_assistant.tracing` | Check that LangSmith tracing is wired up. |
| `uv run langgraph dev` | Open LangGraph Studio on the agent graph. |

## How it works

```
question
  -> agent (LangChain create_agent + InMemorySaver memory)
       -> search_hr_policy tool
            -> Qdrant hybrid retrieve (wide: RERANK_CANDIDATE_K)
            -> Jina reranker (narrow: TOP_K_RESULTS)  ->  cited chunks
  -> Gemini writes the answer from those chunks  ->  answer + citation
```

Ingestion is a **separate** step — `hr_assistant/ingestion.py` is the only
writer to Qdrant. Everything else connects to what it built.

## Documentation

Read `docs/` in order — [01 Overview](docs/01-overview.md)–[08 The Agent](docs/08-the-agent.md)
for this stage. [commands/commands-basic-rag.md](commands/commands-basic-rag.md)
has every provisioning command.
