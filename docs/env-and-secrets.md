# Environment Variables and Secrets

How we store and use configuration and secrets **locally** and **on the server**. Nothing secret is ever committed to Git.

---

## 1. Rule

- **Secrets and real credentials** → only in env files that are **not** in the repo.
- **List of required variables (names only, no values)** → in a committed example file so everyone knows what to set.

---

## 2. Local Development

### 2.1 Where to store

| File | Purpose | In Git? |
|------|---------|--------|
| **`.env`** | Your local dev config (DB, API keys, etc.). Used when you run the app locally. | **No** |
| **`.env.example`** | Template: variable names and placeholder/example values. No real secrets. | **Yes** |

Use **one** `.env` in the project root (or in the backend root if you split backend/frontend later). That keeps “one place for local secrets” and matches the single app layout for now.

### 2.2 Optional: pointing at staging from your machine

If you ever run something **from your PC** that talks to **staging** (e.g. run migrations against the staging DB, or a one-off script):

| File | Purpose | In Git? |
|------|---------|--------|
| **`.env.staging`** | Staging URLs, DB connection, etc. Only for “local command → staging” use. | **No** |

You can create `.env.staging` only when needed. Many setups never need it and only use server-side env on the staging host.

---

## 3. On the Server (staging + prod)

Canonical layout is in [server-layout.md](./server-layout.md).

- Env files live under:
  - **Staging:** **`/srv/tttc/staging/env/`** (e.g. `api.env`)
  - **Prod:** **`/srv/tttc/prod/env/`** (e.g. `api.env`)
- These are created and edited **on the server** (or via deploy that writes them from a secure store). They are **never** in Git.

**Legacy note:** older docs/paths used `/srv/tttc/app/env/` for staging only.

So:

- **Locally:** `.env` (and optionally `.env.staging`) for your machine.
- **Staging:** `/srv/tttc/staging/env/*.env`
- **Prod:** `/srv/tttc/prod/env/*.env`

---

## 4. Summary

| Where | File(s) | Contains | In Git? |
|-------|---------|----------|--------|
| Local dev | `.env` | Real local DB URL, secrets, etc. | No |
| Local → staging | `.env.staging` (optional) | Staging URLs, DB, secrets | No |
| Template | `.env.example` | Variable names + placeholders | Yes |
| Staging server | `/srv/tttc/staging/env/api.env` (etc.) | Real staging config | N/A (not in repo) |
| Prod server | `/srv/tttc/prod/env/api.env` (etc.) | Real prod config | N/A (not in repo) |

---

## 5. .gitignore

The repo **must** ignore any file that could hold secrets. At minimum:

- `.env`
- `.env.local`
- `.env.staging`
- `.env.*.local`
- (and allow `.env.example` to be committed)

A project-level `.gitignore` should include these so they are never committed.
