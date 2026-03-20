# Plan: NetXP Verein CSV → Members Mirror (v1)

## Goal

Implement a **triggerable** process that downloads NetXP Verein’s `AlleMitglieder.csv`, parses it, and **mirrors** member data into our PostgreSQL database.

Constraints and decisions (agreed):

- **No NetXP API**: we import from a full CSV export.
- **Idempotent snapshot sync**: each run is a full snapshot.
- **Unique key**: CSV column **`ID`**.
- **No deletes**: members missing from the latest snapshot become **inactive**.
- **CLI-only for v1**: an HTTP endpoint requires auth; we’ll add it later.
- **Store all columns**: keep all CSV columns per member, but **do not expose sensitive fields** via API.
- **Dry-run**: supported (download + parse + diff + report, no writes).
- **Scale**: ~1k rows currently; still implement streaming-friendly parsing where practical.

---

## Proposed architecture

### 1) Data model

We store:

1. **Typed “query fields”** in dedicated columns for indexing and searching.
2. **Full CSV row** as JSONB (`netxp_raw`) so we keep “everything” without schema churn when NetXP adds/renames columns.

#### `netxp_members` table

- **Primary identity**
  - `id` (uuid or bigserial; internal)
  - `netxp_id` (text, unique) ← CSV `ID`

- **Lifecycle**
  - `is_active` (boolean, indexed) ← derived (not from CSV)
  - `first_seen_at` (timestamptz)
  - `last_seen_at` (timestamptz) ← updated each successful sync when present in CSV
  - `inactive_since` (timestamptz, nullable) ← set when missing from latest CSV

- **Typed fields (from CSV)**
  - `mitgliedsnummer` (text, nullable)
  - `mitgliedsnummer_alphanummerisch` (text, nullable) (optional; present in CSV header)
  - `vorname` (text, nullable)
  - `nachname` (text, nullable)
  - `geburtsdatum` (date, nullable)
  - `eintrittsdatum` (date, nullable)
  - `austrittsdatum` (date, nullable)
  - `mitgliedsart` (text, nullable)
  - `strasse` (text, nullable)
  - `plz` (text, nullable)
  - `ort` (text, nullable)
  - `telefon_privat` (text, nullable)
  - `telefon_arbeit` (text, nullable)
  - `handy` (text, nullable)
  - `email_privat` (text, nullable)
  - `nx_ssp_registration_code` (text, nullable) ← CSV `NxSspRegistrationCode`
  - `beitragsnamen` (text, nullable)
  - `info` (text, nullable)

- **Full row mirror**
  - `netxp_raw` (jsonb, not null) ← all CSV headers/values
  - `netxp_raw_hash` (text, nullable) ← hash of raw row to detect changes cheaply (optional)

- **Timestamps**
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)

Indexes (initial):

- unique: `netxp_id`
- btree: `is_active`
- btree: `(nachname, vorname)` for basic lookups
- (optional) gin: `netxp_raw` if we ever need ad-hoc queries on raw data

#### `netxp_sync_runs` table

Track each run for debugging and observability:

- `id` (uuid/bigserial)
- `started_at`, `finished_at` (timestamptz)
- `status` (text: `success` / `failed` / `dry_run`)
- `source_url` (text, optional; avoid including secrets)
- `download_bytes` (bigint, nullable)
- `encoding_used` (text, nullable)
- `delimiter` (text, default `;`)
- `row_count` (int)
- `inserted_count`, `updated_count`, `unchanged_count`, `inactivated_count` (int)
- `error_count` (int)
- `headers` (jsonb) ← list of CSV headers observed
- `file_hash` (text, nullable) ← hash of the downloaded file (optional)
- `notes` (text, nullable)

---

### 2) Configuration (env vars)

Add names to `.env.example` (no real secrets):

- `NETXP_MEMBERS_CSV_URL` (e.g. `https://store.netxp-verein.de/.../AlleMitglieder.csv`)
- `NETXP_AUTH` (auth string in the form `NETXP_CLUB_ID#NETXP_USERNAME:NETXP_PASSWORD`)
- (optional) `NETXP_TIMEOUT_SECONDS` (default 60)

Notes:

- No credentials in logs.
- Download implemented in Python so it runs on Windows + Linux consistently.

---

## CSV parsing strategy

### Delimiter

- Fixed: `;`

### Encoding (unknown)

Implement a safe “try sequence”:

1. `utf-8-sig`
2. `utf-8`
3. `cp1252` (common for legacy Windows exports in German environments)
4. `latin-1` (last resort; never fails but may mis-decode)

Record the chosen encoding in `netxp_sync_runs.encoding_used`.

### Header handling

- CSV header row provides canonical keys.
- Store headers list in `netxp_sync_runs.headers`.
- For `netxp_raw`, keep a **dict of `{header: value_as_string}`** (after trimming).

### Normalization & typing

Keep `netxp_raw` values as strings (or null), and independently parse typed columns:

- Dates: parse `dd.mm.yyyy` and ISO as fallback.
- Empty strings: treat as null for typed columns.
- Phone/email: store as raw strings (no normalization yet).

### Sensitive fields

- We **store** them (in `netxp_raw`) but **do not expose** in any future API responses by default.
- When we add API endpoints later, we implement an explicit allowlist of fields.

---

## Sync algorithm (v1)

Input: url + credentials from env.

1. **Start a run record** (`netxp_sync_runs`, status pending).
2. **Download** CSV with HTTP client:
   - Use Basic auth derived from `NETXP_AUTH` (split at the last `:` into `auth_user` and `auth_password`).
   - If the server challenges for Digest, fall back to Digest (mirroring curl `--anyauth` behavior).
   - Stream to a temp file (or bytes if small), compute `file_hash`, record `download_bytes`.
3. **Parse CSV**:
   - Detect encoding via try sequence.
   - Read header row; record headers.
   - For each row:
     - Extract `ID` as `netxp_id` (required). If missing: count error, continue.
     - Build `netxp_raw` dict for the row.
     - Map selected typed fields into columns (see list above).
4. **Dry-run mode**
   - Do steps 1–3.
   - Compute diffs vs DB (insert/update/unchanged/inactivate counts).
   - Do **not** write member changes.
   - Store run with `status=dry_run`.
5. **Write mode**
   - Upsert NetXP members by `netxp_id`:
     - Insert if new; set `first_seen_at=now`, `is_active=true`, `last_seen_at=now`.
     - Update if existing; update typed fields + `netxp_raw` + `updated_at`; set `is_active=true`, `last_seen_at=now`, clear `inactive_since`.
     - (Optional optimization) If `netxp_raw_hash` unchanged: count as unchanged; avoid updating.
   - After processing all CSV rows:
     - Inactivate members **not seen in this run**:
       - `is_active=false`, `inactive_since=now` (only if previously active).
6. **Finish run record** with counts, status success/failure, and any notes.

Failure behavior:

- Download errors → run status `failed`, no DB changes.
- Parse errors → continue row-by-row when possible; fail only if header missing or file unreadable.

---

## CLI interface (v1)

Add a module entrypoint inside `api/` so it can be executed on dev/staging/prod:

Example commands (exact naming TBD during implementation):

- Windows (PowerShell, from repo root):
  - `.\api\.venv\Scripts\python.exe -m app.netxp_sync_members` (default: write mode)
  - `.\api\.venv\Scripts\python.exe -m app.netxp_sync_members --dry-run`
  - `.\api\.venv\Scripts\python.exe -m app.netxp_sync_members --limit 50` (optional for testing)
- Linux (server, from `/srv/tttc/staging/api` or `/srv/tttc/prod/api`):
  - `.venv/bin/python -m app.netxp_sync_members`
  - `.venv/bin/python -m app.netxp_sync_members --dry-run`

Exit codes:

- `0` success (including dry-run)
- non-zero on fatal failure (download/parsing cannot proceed)

Output:

- One-line summary: rows, inserted, updated, unchanged, inactivated, errors, duration.

---

## Operator Usage (current v1)

Required env vars:

- `NETXP_MEMBERS_CSV_URL`
- Either:
  - `NETXP_AUTH` (format `NETXP_CLUB_ID#NETXP_USERNAME:NETXP_PASSWORD`),
  - OR `NETXP_CLUB_ID` + `NETXP_USERNAME` + `NETXP_PASSWORD` (separate variables)
- `DATABASE_URL`

Commands:

- Dry-run:
  - `.venv/bin/python -m app.netxp_sync_members --dry-run`
- Write mode:
  - `.venv/bin/python -m app.netxp_sync_members`

Notes:

- `--limit` is only allowed with `--dry-run` (inactivation counts are disabled when `--limit` is used).

---

## Implementation steps (work items)

1. **DB foundation**
   - Introduce a minimal DB module (connection helper using `DATABASE_URL`).
   - Add SQL migrations approach (tiny migration runner + committed `api/migrations/*.sql`).
2. **Schema**
   - Create `netxp_members` and `netxp_sync_runs` tables + indexes.
3. **NetXP download + parse**
   - HTTP download with auth + timeouts.
   - Encoding detection + CSV parsing (`;` delimiter).
4. **Sync logic**
   - Diff + upsert + inactivation.
   - Dry-run mode.
5. **Docs**
   - Update `.env.example` with NetXP var names.
   - Add operator instructions (how to run sync locally and on server).

---

## Open technical check (to resolve during implementation)

NetXP auth method:

- Implementation uses **Basic** first.
- If NetXP returns a `401` with a `WWW-Authenticate: Digest ...` challenge, we retry with **Digest** auth.

