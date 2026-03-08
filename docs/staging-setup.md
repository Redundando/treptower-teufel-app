# Staging Setup (Detailed)

**Treptower Teufel Club App — Staging environment**  
*Complete reference for the current staging server and its configuration.*

---

## 1. Overview

Staging runs on a **single Hetzner Cloud server**. There is no private network, no separate DB server, and no release/rollback layout—by design. The goal is a simple, reproducible environment to develop and test deployment before production.

---

## 2. Hetzner Project

| Item        | Value        |
|------------|--------------|
| **Project name** | Treptower Teufel |
| **Project ID**   | `13723822`       |
| **Console URL**  | https://console.hetzner.com/projects/13723822/dashboard |

---

## 3. Staging Server

### 3.1 Basic Identity

| Item            | Value              |
|-----------------|--------------------|
| **Server name** | `tttc-staging-01`  |
| **Server ID**   | `#123092392`       |
| **Type**        | `CPX22`            |
| **Image**       | Ubuntu 24.04 LTS   |
| **Region**      | Nürnberg (German)  |

*Note: The smallest option at creation time was CPX22, not CPX21.*

### 3.2 Network

| Item           | Value                        |
|----------------|------------------------------|
| **Public IPv4** | `46.225.208.231`            |
| **IPv6 subnet** | `2a01:4f8:1c19:3876::/64`   |

### 3.3 Options Not Used (and Why)

| Option           | Set to | Reason |
|------------------|--------|--------|
| **Private network** | No  | Single server; no internal multi-server communication yet. |
| **Volumes**         | No  | No extra storage need for staging. |
| **Placement groups**| No  | Only relevant for multiple redundant servers. |
| **Labels**          | No  | Not needed for current use; can be added later. |
| **Cloud Config / User Data** | No | Prefer manual, understandable setup first. |
| **SSH key**         | **Yes** | Used for access (see below). |

---

## 4. SSH Access

### 4.1 Key Pair (Windows)

Generated on the Windows machine:

| Key type   | Path (local) |
|-----------|----------------|
| **Private** | `C:\Users\arved\.ssh\teufel_ed25519`   |
| **Public**  | `C:\Users\arved\.ssh\teufel_ed25519.pub` |

Generation command used:

```powershell
ssh-keygen -t ed25519 -C "arved@treptower-teufel"
```

The custom path `C:\Users\arved\.ssh\teufel_ed25519` was specified during generation.

### 4.2 Login

**As root:**

```powershell
ssh -i C:\Users\arved\.ssh\teufel_ed25519 root@46.225.208.231
```

**As normal user (after setup):**

```powershell
ssh -i C:\Users\arved\.ssh\teufel_ed25519 arved@46.225.208.231
```

### 4.3 Normal User

| Item     | Value   |
|----------|---------|
| **Username** | `arved` |
| **Groups**   | `sudo` (for administrative commands) |
| **SSH**      | Same key as root; `authorized_keys` copied into `/home/arved/.ssh/`. |

Administrative tasks (`apt install`, `ufw`, user management, hostname, etc.) require root or `sudo`—this is expected.

---

## 5. Base Server Setup (Commands Used)

The following was run on the server (as root or with `sudo` where needed).

### 5.1 System Update

```bash
apt update && apt upgrade -y
```

### 5.2 Timezone

```bash
timedatectl set-timezone Europe/Berlin
```

### 5.3 Hostname

```bash
hostnamectl set-hostname tttc-staging-01
```

### 5.4 Create Normal User and SSH Access

```bash
adduser arved
usermod -aG sudo arved
mkdir -p /home/arved/.ssh
cp /root/.ssh/authorized_keys /home/arved/.ssh/
chown -R arved:arved /home/arved/.ssh
chmod 700 /home/arved/.ssh
chmod 600 /home/arved/.ssh/authorized_keys
```

---

## 6. Firewall (UFW)

UFW is installed and enabled.

### 6.1 Allowed Ports

| Port / Service | Purpose    |
|----------------|------------|
| **OpenSSH**    | SSH        |
| **80/tcp**     | HTTP       |
| **443/tcp**    | HTTPS      |

### 6.2 Commands Used

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

---

## 7. Installed Software and Versions

### 7.1 Python

| Item    | Value        |
|---------|--------------|
| **Version** | Python 3.12.3 |
| **Check**   | `python3 --version` |

**Decision:** Stay on 3.12 (Ubuntu 24.04 default); do not move to 3.13 yet—stability and FastAPI compatibility were prioritised.

### 7.2 PostgreSQL

| Item   | Value |
|--------|--------|
| **Installation** | `postgresql` + `postgresql-contrib` |
| **Service**      | Enabled and started via systemd |

**Commands used:**

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 7.3 Database and User (Staging)

| Item       | Value              |
|------------|--------------------|
| **Database name** | `tttc_staging`     |
| **DB user**       | `tttc_staging_user` |
| **Password**      | *Not stored in docs; set during setup.* |

**Creation pattern (run as PostgreSQL superuser):**

```sql
CREATE USER tttc_staging_user WITH ENCRYPTED PASSWORD '<PASSWORT>';
CREATE DATABASE tttc_staging OWNER tttc_staging_user;
```

Connection from the app will use this user and database. The password is only in a secure place (e.g. env or secrets), not in this document.

### 7.4 Python Virtual Environment

| Item   | Value                          |
|--------|---------------------------------|
| **Path** | `/srv/tttc/app/api/.venv`     |

Created and used for the FastAPI application under `/srv/tttc/app/api`.

### 7.5 FastAPI (Proof of Concept)

A minimal FastAPI app was added to verify the stack. Example:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

The `/health` endpoint was tested successfully. This was only a PoC; the real project layout and app will come from the local repo and deploy.

### 7.6 Node.js

Node.js is installed for:

- Frontend tooling and builds  
- **Not** as the backend runtime (backend remains Python/FastAPI)

The exact Node version was not recorded in the reference notes; it can be checked on the server with `node --version` and `npm --version`.

### 7.7 Caddy (Reverse Proxy)

**Status:** Not fully set up yet. Caddy is planned for reverse proxy, HTTPS, and routing to backend/frontend. Installation and configuration are a later step.

---

## 8. Directory Structure on the Server

The chosen layout under `/srv/tttc` is flat and simple (no release/current/shared model for staging).

### 8.1 Target Structure

```text
/srv/tttc
└── app
    ├── api          ← Backend code + Python .venv
    ├── web          ← Frontend code (built assets or source, depending on deploy)
    ├── env          ← Server-side .env files (not in Git)
    └── logs         ← Log files
```

### 8.2 Meaning of Each Directory

| Path              | Purpose |
|-------------------|--------|
| `/srv/tttc/app/api`  | FastAPI application and its virtualenv (e.g. `.venv`). |
| `/srv/tttc/app/web`  | Frontend application or built output. |
| `/srv/tttc/app/env`  | Environment files (e.g. `api.env`, `web.env`); never committed. |
| `/srv/tttc/app/logs` | Application log files. |

### 8.3 Why No Release Model on Staging

- Staging should stay simple.  
- No rollback or multi-release layout required yet.  
- A single target path per app (api, web) is enough.  
- A proper release/current/shared model can be introduced for production later.

---

## 9. What Exists vs What Does Not (As of This Doc)

### 9.1 Already in Place

- Hetzner project “Treptower Teufel”
- Staging server `tttc-staging-01` (CPX22, Ubuntu 24.04, Nürnberg)
- Public access via IPv4 (and IPv6 network)
- SSH key and user `arved` with sudo
- UFW enabled (SSH, 80, 443)
- PostgreSQL installed; DB `tttc_staging` and user `tttc_staging_user` created
- Python 3.12.3
- Virtualenv at `/srv/tttc/app/api/.venv`
- Minimal FastAPI health check run successfully
- Node.js installed
- Directory structure under `/srv/tttc/app` as above

### 9.2 Not Yet Done / Not Final

- Real local project (backend + frontend as proper projects)
- Real deploy process (from local repo to server)
- Caddy installed and configured
- systemd units for the app (FastAPI, and optionally frontend)
- Frontend project (Svelte/SvelteKit) and its deploy
- Domain/subdomain and routing (e.g. staging-app, staging-api)
- Finalised secrets/env layout (e.g. `api.env`, `web.env` under `/srv/tttc/app/env`)
- Production environment (separate doc)

---

## 10. Credentials and Sensitive Data (Summary)

**Documented here (safe):**

- Project ID, server name, ID, type, IPv4, IPv6
- SSH user names and key paths (not the private key itself)
- DB name and DB user name
- Directory layout and versions (Python, PostgreSQL concept)

**Intentionally not in this document:**

- PostgreSQL password for `tttc_staging_user`
- Future API secrets and tokens
- Contents of `.env` or env files
- Domain provider or Hetzner account credentials
- Any deploy keys beyond the SSH key path already mentioned

---

## 11. Quick Reference Table

| Topic        | Value / Location |
|-------------|-------------------|
| **Server**  | `tttc-staging-01`, ID `123092392`, `46.225.208.231` |
| **SSH**     | `arved` or `root`, key: `C:\Users\arved\.ssh\teufel_ed25519` |
| **Python**  | 3.12.3 |
| **Venv**    | `/srv/tttc/app/api/.venv` |
| **PostgreSQL** | DB: `tttc_staging`, User: `tttc_staging_user` |
| **App dirs**   | `/srv/tttc/app/{api,web,env,logs}` |
| **Caddy**   | Not yet configured |
| **systemd** | Not yet configured |

---

*This document describes the staging setup as it was established. For philosophy and “what/why”, see [philosophy.md](./philosophy.md). For next steps (local dev, deploy, Caddy, systemd), see the main project plan or task list.*
