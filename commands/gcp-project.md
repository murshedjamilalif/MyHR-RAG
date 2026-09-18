# GCP project settings — MyHR-RAG

Values copied from Google Cloud Console for **this** machine. Put the
non-secret ones in `.env`. Secrets (Jina, Qdrant, LangSmith) stay in `.env`
only — never in this file.

Use **these** IDs, not the demo `rag-hr-assistant-demo*` values in
[commands-basic-rag.md](commands-basic-rag.md).

---

## Console → what we copied

| Console label | Value | Used as |
|---|---|---|
| Project name | `MyHR-RAG` | Display name only (not in `.env`) |
| Project number | `434830168266` | Rarely needed; some APIs show it |
| Project ID | `myhr-rag` | `PROJECT_ID` **and** `GCS_BUCKET_NAME` |

A GCP **project has no single location**. Name, number, and ID are global.
Region is chosen **per product** (Vertex AI, Cloud Storage, Cloud Run).

---

## Beginner: where does `us-central1` come from?

You already found it for the **bucket** (Cloud Storage → Create → Location).
Vertex AI has **the same kind of dropdown**, on a **different page**. Nothing
copies the bucket’s region into Vertex automatically.

Google’s data centers have **codes**. `us-central1` means **Iowa**. The same
code is reused by many products. That is why LOCATION, REGION, and the bucket
`--location` can all say `us-central1` — one Iowa campus, three products.

| Product | Console: where you *see the list* and pick | What you put in `.env` / the command |
|---|---|---|
| Cloud Storage | **Cloud Storage → Create bucket → Location type: Region** | `--location=us-central1` (not a `.env` region field) |
| **Vertex AI (Gemini)** | Search **Vertex AI** → open it → **region dropdown at the top** | `LOCATION=us-central1` |
| Cloud Run (later) | **Cloud Run → Deploy → Region** | `REGION=us-central1` |

### Click path for Vertex AI (this is the one you were missing)

1. Open [Google Cloud Console](https://console.cloud.google.com) with project `myhr-rag`.
2. Search bar at the top: type **Vertex AI** → open **Vertex AI**.
3. Look at the **top of the Vertex AI page** (same row as the project picker).
   There is a **location / region** control. Open it.
4. You will see names like:
   - `us-central1 (Iowa)`
   - `us-east1 (South Carolina)`
   - `europe-west1 (Belgium)`
   - `asia-southeast1 (Singapore)`
5. Click **`us-central1 (Iowa)`**. That string `us-central1` is what goes in
   `.env` as `LOCATION`.

You are not “getting” this value from the bucket or from Project Settings.
You are **looking at Vertex AI’s own region list** — the list of places
Google will run Gemini for you.

Full catalog (which models exist in which region):
[Vertex AI locations](https://cloud.google.com/vertex-ai/docs/general/locations).

### Why this tutorial uses `us-central1`

It is a common default, Gemini on Vertex is available there, and the course
files already use it. As a beginner, **type `us-central1` in all three
places** (Vertex `LOCATION`, Cloud Run `REGION`, bucket `--location`). Do not
pick three different regions.

`LOCATION` and `REGION` in `.env` look duplicated on purpose: same Iowa
code, **two labels**, not two places on the map. You will not see two
different regions in the console if you followed this project.

---

## The three knobs: Vertex `LOCATION`, Cloud Run `REGION`, bucket `--location`

There is **one** data center: **Iowa**, code **`us-central1`**. You pick
that once. You then tell **three Google products** about it, with **three
separate knobs**. None of them copies the others. You will not see three
cities in the console — you will see `us-central1` three times, on three
screens.

```
                    us-central1  (Iowa)
                           |
         +-----------------+-----------------+
         |                 |                 |
   Vertex AI          Cloud Run         Cloud Storage
   Gemini model       the website       your files
   LOCATION           REGION            --location
   (.env)             (.env)            (create command only)
```

| Knob | Product | What you put in Iowa | Where you pick it | When it matters |
|---|---|---|---|---|
| 1. `LOCATION` | **Vertex AI** | The **Gemini** LLM | Vertex AI → region dropdown at the **top** | Every question (Python) |
| 2. `REGION` | **Cloud Run** | The **deployed app** (container) | Cloud Run → Deploy → Region | Later, when you deploy |
| 3. `--location` | **Cloud Storage** | **Documents** in `gs://myhr-rag` | Cloud Storage → Create bucket → Location | Once, when you create the bucket |

`GCS_BUCKET_NAME=myhr-rag` is **not** a fourth location. It is only the
bucket’s **name**.

They do **not** set each other. Type `us-central1` in all three so the
model, the website, and the files stay in the same Iowa campus.

---

### 1. Vertex `LOCATION` (Gemini)

```env
LOCATION=us-central1
```

| | |
|---|---|
| Product | Vertex AI |
| What lives in Iowa | The **Gemini model** |
| Who reads it | Python (`langchain-google-genai`), on **every question** |
| Console | Search **Vertex AI** → open it → **region dropdown at the top** |
| Docs | [Vertex AI locations](https://cloud.google.com/vertex-ai/docs/general/locations) |
| Does it set the bucket? | **No** |
| Does it set Cloud Run? | **No** |

If this is missing or wrong, ingest into GCS can still work, but calling
Gemini fails or hits the wrong region.

**This stage (basic RAG) needs this one.**

---

### 2. Cloud Run `REGION` (the website, later)

```env
REGION=us-central1
```

| | |
|---|---|
| Product | Cloud Run |
| What lives in Iowa | Your **running app** (Streamlit/API in a container on Google’s servers) |
| Who reads it | `gcloud run deploy --region=…` in the deployment commands — **not** the local Python app |
| Console | **Cloud Run → Deploy revision / Create service → Region** |
| Docs | [Cloud Run locations](https://cloud.google.com/run/docs/locations) |
| Does it set Vertex? | **No** |
| Does it set the bucket? | **No** |

Cloud Run is “put this program on the internet.” Region = which Iowa (or
other) campus hosts that program. Local `uv run streamlit run app.py` does
**not** use `REGION`.

**This stage (basic RAG) can ignore it.** Keep the value equal to
`LOCATION` so you do not forget later. It is still Iowa, not a second city.

---

### 3. Bucket `--location` (Cloud Storage files)

```powershell
gcloud storage buckets create gs://myhr-rag `
  --project=myhr-rag `
  --location=us-central1
```

| Flag | Meaning |
|---|---|
| `gs://myhr-rag` | Bucket **name** (`GCS_BUCKET_NAME`) |
| `--project=myhr-rag` | Which GCP project owns it |
| `--location=us-central1` | Where **files** live (Iowa) |

| | |
|---|---|
| Product | Cloud Storage |
| What lives in Iowa | Policy **documents** (`raw/`, `processed/`) |
| Who reads it | Only this **create** command. After that, GCP remembers it **on the bucket** |
| Console | **Cloud Storage → Create bucket → Location type: Region → us-central1 (Iowa)** |
| In `.env`? | **No.** `.env` has the **name** only (`GCS_BUCKET_NAME`) |
| Does it set Vertex? | **No** |
| Does it set Cloud Run? | **No** |

If you omit `--location`, create fails or Google picks a default you did
not intend. You **cannot change** a bucket’s location later.

**This stage needs this once**, when you create `gs://myhr-rag`.

---

### All three at a glance

| | Vertex `LOCATION` | Cloud Run `REGION` | Bucket `--location` |
|---|---|---|---|
| `.env` key | `LOCATION=us-central1` | `REGION=us-central1` | *(none — not in `.env`)* |
| Product | Vertex AI | Cloud Run | Cloud Storage |
| Places in Iowa | **Gemini** | **Deployed website** | **Files** |
| Needed for basic RAG now? | **Yes** | No (later) | **Yes** (create once) |
| Sets the other two? | No | No | No |

Same value everywhere **on purpose**: one Iowa campus for model + app +
files.

---



## `.env` — what each line means


```env
PROJECT_ID=myhr-rag
LOCATION=us-central1
REGION=us-central1
GCS_BUCKET_NAME=myhr-rag
```

`#` in `.env` starts a **comment**. It does **not** disable the variable.

```env
LOCATION=us-central1     # Vertex AI region
REGION=us-central1       # Cloud Run deploy region
```

- **Set:** the values before `#` (these are live)
- **Ignore:** the words after `#` (human notes only)

| Variable | What it is | Where you pick it | What it is not |
|---|---|---|---|
| `PROJECT_ID` | GCP project ID | IAM & Admin → Settings | Not a region |
| `LOCATION` | Vertex AI / Gemini region (the **app** reads this) | Vertex AI page → **top region dropdown** | Not the bucket location |
| `REGION` | Cloud Run deploy region (gcloud / later phase) | Cloud Run → Deploy → Region | Not used by basic RAG Python yet |
| `GCS_BUCKET_NAME` | Bucket **name** → `gs://myhr-rag` | You chose it (= project ID) | Not a region |

The bucket’s region is **not** a `.env` key. It is set at create time:

`--location=us-central1` on `gcloud storage buckets create` (Cloud Storage → Create → Location).

---

## Where `--location` / region comes from

You do **not** copy it from **IAM & Admin → Settings**. That page has no
region.

`--location=us-central1` is a **choice**. This project uses `us-central1`
(Iowa) because `.env` `LOCATION` is the Vertex AI region, and the bucket
should match.

### See it

**Console**

- **IAM & Admin → Settings** — name, number, ID. No region.
- **Vertex AI** — region dropdown at the top → `us-central1 (Iowa)`.
- **Cloud Storage → Create bucket** — Location type: Region → same dropdown.
  That dropdown **is** the list of bucket locations.

**Terminal**

```powershell
gcloud config get-value project
gcloud config get-value compute/region
gcloud compute regions list
```

Empty `compute/region` is normal until you set it. The Python app does **not**
read that; it reads `LOCATION` from `.env`.

### Set it

```powershell
gcloud config set project myhr-rag
gcloud config set compute/region us-central1
```

After the bucket exists:

```powershell
gcloud storage buckets describe gs://myhr-rag --format="value(name,location)"
```

You cannot change a bucket’s location later. Create a new bucket if you
picked the wrong region.

---

## Bucket name = project ID

`GCS_BUCKET_NAME` is the **same string** as the project ID:

```text
gs://myhr-rag
```

Names are globally unique. If create fails, that ID is already taken worldwide.

```powershell
gcloud storage buckets create gs://myhr-rag `
  --project=myhr-rag `
  --location=us-central1
```

| Flag | Value | Source |
|---|---|---|
| `--project` | `myhr-rag` | Console → Project ID |
| `gs://myhr-rag` | bucket name | Same as Project ID (our choice) |
| `--location` | `us-central1` | **You pick it** (match Vertex). Not on the project settings page. |

`ingest.py` creates `raw/` and `processed/` inside the bucket. You do not
create those folders by hand.

---

## Relationship: bucket vs Vertex AI

They are **two different GCP services** in the same project. The bucket does
not belong to Vertex AI. Vertex AI does **not** automatically read the bucket.

```
local data/
    → Cloud Storage (gs://myhr-rag)     documents: raw/ then processed JSON
    → embeddings (Jina) + Qdrant        vectors for search
    → Vertex AI Gemini                  writes the answer from retrieved chunks
```

| | **Cloud Storage (bucket)** | **Vertex AI** |
|---|---|---|
| Job | Store **documents** | Run **Gemini** (the LLM) |
| `.env` | `GCS_BUCKET_NAME=myhr-rag` | `LOCATION=us-central1` |
| Python | `google-cloud-storage` | `langchain-google-genai` |
| When | Ingest (`ingest.py`) | Each question |

**What they share**

- Same project `myhr-rag` (billing, ADC login)
- Same region **by choice**: `us-central1`

**What they do not share**

- Gemini does **not** scan `gs://myhr-rag`
- The bucket does **not** host the model
- Search goes through **Qdrant** (vectors) and **Jina** (rerank)
- Gemini only sees **chunks** the agent puts in the prompt

Bucket = library of policy files. Vertex = model that writes the cited
answer. The Python app is the glue.

---

## Other IDs already on this machine

```text
PROJECT_ID=myhr-rag
PROJECT_NUMBER=434830168266
REGION=us-central1
LOCATION=us-central1
GCS_BUCKET_NAME=myhr-rag
BILLING_ACCOUNT_ID=01C1BA-71A95A-C16402
QDRANT_COLLECTION_NAME=hr_policies
QDRANT_NOISY_COLLECTION_NAME=hr_policies_noisy_demo
```

Billing list (does not charge):

```powershell
gcloud billing accounts list
```

Link the project to billing before Vertex / GCS will accept paid API calls:

```powershell
gcloud billing projects link myhr-rag --billing-account=01C1BA-71A95A-C16402
```

Full provisioning (APIs, ADC, ingest): [commands-basic-rag.md](commands-basic-rag.md),
[README.md](../README.md). `.env` comments: [../.env.example](../.env.example).
