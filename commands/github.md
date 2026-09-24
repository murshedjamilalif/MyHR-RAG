# Git / GitHub commands used for MyHR-RAG

Remote: https://github.com/murshedjamilalif/MyHR-RAG.git

Run from the project root: `D:\CODE\AI\Projects\MyHR`

`.env` and `.venv` were **not** committed (see `.gitignore`).

---

## 1. Ignore secrets and local junk

Created `.gitignore` so these stay off GitHub:

- `.env` / `.env.local`
- `.venv/`
- `__pycache__/`, `*.pyc`
- `.streamlit/secrets.toml`
- `*.pdf`

`.env.example` **is** committed (placeholders only).

---

## 2. New local repo + first commit

```bash
git init
git add .
git status
git commit -m "Initial commit: MyHR RAG project, config, and local setup notes."
```

`git status` was used to confirm `.env` and `.venv` were unstaged.

---

## 3. Default branch = `main`

Git started on `master`. Rename:

```bash
git branch -M main
```

---

## 4. Three stage branches

All created from that first commit (same code until they diverge):

```bash
git branch basic-rag
git branch ai-security
git branch deployment
```

| Branch | Use |
|---|---|
| `main` | GitHub default |
| `basic-rag` | current work (`myhr_rag`) |
| `ai-security` | later |
| `deployment` | later |

---

## 5. Point at GitHub

```bash
git remote add origin https://github.com/murshedjamilalif/MyHR-RAG.git
```

(Skip this if `origin` already exists: `git remote -v`.)

---

## 6. Push every branch

```bash
git push -u origin main
git push -u origin basic-rag
git push -u origin ai-security
git push -u origin deployment
```

`-u` sets upstream so later you can use `git push` / `git pull` with no extra args.

---

## 7. Work on basic-rag

```bash
git checkout basic-rag
```

Current working branch is **`basic-rag`**. Security and deploy updates wait until that branch is checked out.

---

## Everyday commands after this

```bash
git status
git add <files>
git commit -m "your message"
git push
```

Switch stage:

```bash
git checkout ai-security
git checkout deployment
git checkout basic-rag
```

See branches:

```bash
git branch -vv
```

---

## Repo

https://github.com/murshedjamilalif/MyHR-RAG
