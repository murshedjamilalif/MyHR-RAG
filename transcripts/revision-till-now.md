# Revision — এখন পর্যন্ত যা হয়েছে

এই ফাইলটা **revise** করার জন্য। এখানে আছে: আপনি কী কী **complete** করেছেন, **কেন** করেছেন, আর কোথায় **stuck** হয়েছিলেন। Command copy-paste করা যাবে; মূল কাজ হলো concept পরিষ্কার রাখা।

**Status:** local Python + GCP login + `.env` এর ID গুলো ready। Bucket create, Qdrant / Jina key, ingest — **এখনো pending**।

---

## ৩০ সেকেন্ডের map (মাথায় রাখুন)

```
আপনার laptop
  ├── uv + .venv (MyHR)     → Python packages
  ├── gcloud (Windows)      → GCP CLI  (venv-এর ভিতরে না)
  └── .env                  → app যে values পড়ে

Google Cloud project: myhr-rag
  ├── Vertex AI Gemini      → LOCATION=us-central1    (model)
  ├── Cloud Storage bucket  → --location=us-central1  (files)  ← create বাকি
  └── Cloud Run             → REGION=us-central1      (website, পরে)

বাইরে: Qdrant (vectors) + Jina (embed / rerank) + optional LangSmith
```

পরে pipeline: `data/` → GCS → Jina embed → Qdrant → question → Gemini answer।

---

## Console থেকে নেওয়া ID

| Console-এ যা দেখেছেন | Value | কোথায় ব্যবহার |
|---|---|---|
| Project **name** | `MyHR-RAG` | শুধু display — `.env`-এ নেই |
| Project **number** | `434830168266` | খুব কম লাগে |
| Project **ID** | `myhr-rag` | `PROJECT_ID` **এবং** `GCS_BUCKET_NAME` |
| Billing account | `01C1BA-71A95A-C16402` | `gcloud billing projects link` |
| Region code | `us-central1` = **Iowa** | তিনটা product, **একটাই** city |

**মনে রাখবেন:** GCP **project-এর কোনো একটা fixed location নেই**। Name, number, ID global। Region **প্রতিটা product আলাদা** বেছে নিতে হয় (Vertex page, bucket create, Cloud Run deploy — তিনটা **আলাদা dropdown**, একই code)।

---

## Step 1 — uv + venv  ✅ complete

**কেন:** Python packages এই project-এর ভিতরে রাখা, system Python নষ্ট না করা।

```powershell
uv venv
.venv\Scripts\activate          # PowerShell
uv pip install -r requirements.txt
```

Git Bash: `source .venv/Scripts/activate`

Prompt-এ `(MyHR)` এলে venv চালু।

**Concept:** `requirements.txt`-এর জিনিস (যেমন `google-cloud-storage`) **venv-এর ভিতরে**। `gcloud` / `git` / `uv` **venv-এ নেই** — এগুলো Windows program।

---

## Step 2 — `gcloud` install + PATH  ✅ complete (কষ্ট করে)

**কেন:** terminal থেকে project set, login, bucket create।

```powershell
winget install Google.CloudSDK
```

আপনার PC-তে **আগেই installed** ছিল (winget নতুন করে বসায়নি)। Path:

`C:\Users\USER\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin`

**আপনি যে error দেখেছেন:** `gcloud` is not recognized / `command not found`।

**Lesson:** PATH **প্রতিটা shell-এ আলাদা**।

| Shell | এই session-এ PATH |
|---|---|
| PowerShell | `$env:Path += ";$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"` |
| cmd | `set PATH=%PATH%;%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin` |
| Git Bash (`MINGW64`) | `export PATH="$PATH:/c/Users/USER/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin"` |

PowerShell-এ PATH থাকলেও **Git Bash-এ automatically আসে না**।

cmd-এ `$env:Path` চালালে error: *filename … syntax is incorrect* — কারণ সেটা PowerShell-এর syntax।

Check: `gcloud --version` → SDK 584.0.0 পেলে ঠিক আছে।

---

## Step 3 — project select  ✅ complete

```powershell
gcloud config set project myhr-rag
```

Expected: `Updated property [core/project].`

**কেন:** পরের `gcloud` command, quota, billing — সব `myhr-rag` target করবে। না হলে “no project”।

---

## Step 4 — দুই ধরনের login (এখানেই confusion)

Google-এ **দুই রকম login**। দুটোই লাগে, কাজ আলাদা।

### A) ADC — Python-এর জন্য  ✅ complete

```powershell
gcloud auth application-default login
gcloud auth application-default set-quota-project myhr-rag
```

Browser খুলবে। Credentials save হয় এখানে:

`%APPDATA%\gcloud\application_default_credentials.json`

**কেন:** `ingest.py` / Streamlit / agent **Python library** দিয়ে Vertex আর GCS call করে। তারা `gcloud` prompt পড়ে না — এই **ADC file** পড়ে।

Quota project = bill / quota `myhr-rag`-এ যাবে।

### B) CLI login — `gcloud` command-এর জন্য  ✅ complete

ADC থাকার পরেও `gcloud billing accounts list` fail হয়েছিল:

`You do not currently have an active account selected.`

**কেন:** billing, `gcloud storage`, services enable — এগুলোর জন্য **CLI** login লাগে।

```powershell
gcloud auth login
```

Expected: `You are now logged in as [your-email]. Current project [myhr-rag].`

### বড় pitfall ⚠️

Google লেখে: `gcloud config set account ACCOUNT`

আপনি **আক্ষরিকভাবে** `ACCOUNT` টাইপ করেছিলেন। সেটা placeholder — জায়গায় **আসল email** বসাতে হয়।

Result: active account হয়ে গেল string `ACCOUNT` → *does not have any valid credentials*।

**Fix (আপনি করেছেন):**

```powershell
gcloud config set account murshedjamilalif@gmail.com
gcloud billing accounts list
```

Check: `gcloud auth list` — যেটার সামনে `*`, সেটাই active।

---

## Step 5 — billing list  ✅ complete

```powershell
gcloud billing accounts list
```

আপনার output:

```
ACCOUNT_ID            NAME                OPEN
01C1BA-71A95A-C16402  My Billing Account  True
```

**কেন:** Vertex / GCS paid API — project **link** না থাকলে কাজ করে না। List করা **charge করে না**। `OPEN` অবশ্যই `True` হতে হবে।

**বাকি (যদি এখনো না করে থাকেন):**

```powershell
gcloud billing projects link myhr-rag --billing-account=01C1BA-71A95A-C16402
```

---

## Step 6 — `.env` IDs  ✅ complete (keys এখনো placeholder)

```env
PROJECT_ID=myhr-rag
LOCATION=us-central1      # Vertex Gemini — app এটা পড়ে
REGION=us-central1        # Cloud Run — পরে; এখন ignore
GCS_BUCKET_NAME=myhr-rag  # bucket-এর *name* মাত্র → gs://myhr-rag
```

`#` মানে comment — variable **বন্ধ করে না**। `LOCATION=us-central1` live।

Jina / Qdrant / LangSmith এখনো `your-…-here` — **আসল key paste করা বাকি**।

---

## Step 7 — তিনটা “location” (আসলে একটাই Iowa)  ✅ concept complete

**দুইটা location নেই।** Map-এ **একটা** জায়গা: Iowa, code `us-central1`। তিনটা **product-কে আলাদা করে বলতে হয়**।

```
              us-central1 (Iowa)
                     |
     +---------------+---------------+
     |               |               |
 Vertex AI      Cloud Run      Cloud Storage
 Gemini model   website (পরে)   আপনার files
 LOCATION       REGION         --location
 (.env)         (.env)         (create command)
```

| Knob | Product | Iowa-তে কী থাকে | কোথায় set | এখন দরকার? |
|---|---|---|---|---|
| `LOCATION` | Vertex AI | **Gemini model** | `.env` ← Vertex AI page-এর **উপরের dropdown** | **হ্যাঁ** |
| `REGION` | Cloud Run | **Deployed app** | `.env` ← Cloud Run → Deploy → Region | না (local Streamlit এটা ব্যবহার করে না) |
| `--location` | Cloud Storage | **Files** `gs://myhr-rag` | bucket **create** command | **হ্যাঁ**, একবার |

কেউ কারো থেকে **copy হয় না**। তিন জায়গায় `us-central1` নিজে লিখুন — একই campus, latency আর সরলতার জন্য।

### Vertex `LOCATION` কোথায় পাবেন?

Project Settings page-এ **নেই**। Bucket থেকেও **copy হয় না**।

1. Console → search **Vertex AI**
2. Page-এর **উপরে** region dropdown
3. `us-central1 (Iowa)` select
4. `.env`-এ `LOCATION=us-central1`

List: https://cloud.google.com/vertex-ai/docs/general/locations

### Bucket `--location` কী?

এই command-এর `--location` **শুধু Cloud Storage**:

```bash
gcloud storage buckets create gs://myhr-rag --project=myhr-rag --location=us-central1
```

| Flag | অর্থ |
|---|---|
| `gs://myhr-rag` | bucket-এর **name** (`GCS_BUCKET_NAME`) |
| `--project=myhr-rag` | কোন GCP project |
| `--location=us-central1` | **files** Iowa-তে |

`.env`-এর `LOCATION` এই command **পড়ে না**। এই command Vertex **set করে না**।

Bucket-এর location create-এর পরে **বদলানো যায় না**।

### Bucket আর Vertex — সম্পর্ক

দুটো **আলাদা service**, একই project।

- Bucket = library (documents)
- Vertex = Gemini (উত্তর লেখে)
- Qdrant + Jina = search / rerank
- Python app = glue

Gemini **নিজে থেকে** `gs://myhr-rag` scan করে না।

---

## Step 8 — Git Bash-এ bucket create  ❌ fail (syntax + PATH)

আপনি Git Bash (`MINGW64`)-এ PowerShell-এর backtick (`` ` ``) paste করেছিলেন।

Bash-এ backtick মানে “এই লাইনকে command হিসেবে চালাও”। তাই:

```
bash: gcloud: command not found
bash: --project=myhr-rag: command not found
bash: --location=us-central1: command not found
```

**দুইটা bug একসাথে:** (1) Git Bash PATH-এ `gcloud` নেই (2) PowerShell-এর line-break Bash-এ দেওয়া।

**ঠিক version — এক লাইন (সব shell-এ):**

```bash
export PATH="$PATH:/c/Users/USER/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin"
gcloud storage buckets create gs://myhr-rag --project=myhr-rag --location=us-central1
```

Git Bash-এ লাইন ভাঙতে হলে **backslash** `\`, backtick না।

PowerShell-এ backtick ঠিক আছে।

Confirm:

```bash
gcloud storage buckets describe gs://myhr-rag --format="value(name,location)"
```

Name globally unique। `myhr-rag` already taken হলে অন্য name নিতে হবে।

---

## Quiz — নিজেকে জিজ্ঞেস করুন

1. `(MyHR)` prompt-এ `gcloud` কেন নাও থাকতে পারে?  
   → venv শুধু Python; `gcloud` Windows PATH-এ থাকে।

2. ADC আর `gcloud auth login`-এর পার্থক্য?  
   → ADC = Python libraries। CLI login = `gcloud billing` / `gcloud storage`।

3. `LOCATION` আর `--location` কি একই জিনিস?  
   → **Value** এক (`us-central1`)। **Product** আলাদা (Vertex vs bucket)।

4. `GCS_BUCKET_NAME` কি region?  
   → না। শুধু **name** (`gs://myhr-rag`)।

5. Git Bash-এ `` ` `` দিলে কী হয়?  
   → Bash সেটাকে command substitution মনে করে; `--project=…`-কে program হিসেবে চালায়।

6. Project Settings-এ region কোথায়?  
   → **নেই।** Vertex dropdown / bucket create / Cloud Run deploy — আলাদা আলাদা page।

---

## Next (এখনো করা হয়নি)

1. Billing **link** (যদি pending থাকে)
2. API enable: `aiplatform.googleapis.com` + `storage.googleapis.com`
3. Bucket **সফলভাবে create** (`gs://myhr-rag`)
4. Qdrant cluster + URL / API key → `.env`
5. Jina API key → `.env`
6. Optional LangSmith
7. `hr_assistant/config.py` + ingest

---

## Related files

| File | কী আছে |
|---|---|
| `.env` | আপনার আসল ID (keys বাকি) |
| [commands/gcp-project.md](../commands/gcp-project.md) | ID + তিনটা knob, বিস্তারিত (English) |
| [transcripts/Configure project settings.md](Configure%20project%20settings.md) | video notes: bucket, Qdrant, Jina, LangSmith |
| [README.md](../README.md) | project overview + Windows `gcloud` PATH (PowerShell / cmd) |
| [commands/commands-basic-rag.md](../commands/commands-basic-rag.md) | demo ID — **ব্যবহার করবেন না**; আপনার ID `myhr-rag` |
