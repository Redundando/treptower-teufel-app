# systemd on staging (API + frontend as services)

**Why:** Right now the deploy script starts the API and frontend with `nohup`. They stop when the server reboots and there’s no clean “restart.” With systemd you get:

- **Start on boot** — API and web come up after a reboot.
- **Clean restarts** — `systemctl restart tttc-api` / `tttc-web` instead of pkill + nohup.
- **Optional auto-restart** if a process crashes.
- **Logs** via `journalctl -u tttc-api` / `tttc-web` (or keep file logs).

**When:** Do this once on the server. After that, the deploy script will use `systemctl restart` instead of nohup.

---

## 1. Unit files (in the repo)

**Legacy (single tree `/srv/tttc/app`):**

- **`tttc-api.service`**, **`tttc-web.service`**

**Target layout (`/srv/tttc/staging` + `/srv/tttc/prod`):**

- **`tttc-api-staging.service`**, **`tttc-web-staging.service`** — ports 8000 / 5173
- **`tttc-api-prod.service`**, **`tttc-web-prod.service`** — ports 8001 / 5174

All under **`ops/systemd/`**. User `arved`; paths in [server-layout.md](./server-layout.md).

---

## 2. One-time setup on the server

SSH in, then:

### 2.1 Current setup (staging + prod)

**Copy the unit files**

```bash
sudo cp /srv/tttc/staging/repo/ops/systemd/tttc-api-staging.service /etc/systemd/system/
sudo cp /srv/tttc/staging/repo/ops/systemd/tttc-web-staging.service /etc/systemd/system/
sudo cp /srv/tttc/prod/repo/ops/systemd/tttc-api-prod.service /etc/systemd/system/
sudo cp /srv/tttc/prod/repo/ops/systemd/tttc-web-prod.service /etc/systemd/system/
sudo systemctl daemon-reload
```

**Enable and start**

```bash
sudo systemctl enable tttc-api-staging tttc-web-staging tttc-api-prod tttc-web-prod
sudo systemctl start tttc-api-staging tttc-web-staging tttc-api-prod tttc-web-prod
sudo systemctl status tttc-api-staging tttc-web-staging tttc-api-prod tttc-web-prod
```

**Check**

- Staging API: `curl -s http://localhost:8000/health` → `{"status":"ok"}`
- Staging web: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5173` → 200
- Prod API: `curl -s http://localhost:8001/health` → `{"status":"ok"}`
- Prod web: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5174` → 200

After this, the **deploy script** will restart these services instead of starting processes with nohup.

### 2.2 Legacy setup (`/srv/tttc/app`)

If you still run the old single-tree staging layout, the legacy unit files are:

```bash
sudo cp /srv/tttc/app/repo/ops/systemd/tttc-api.service /etc/systemd/system/
sudo cp /srv/tttc/app/repo/ops/systemd/tttc-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tttc-api tttc-web
sudo systemctl start tttc-api tttc-web
```

---

## 3. Useful commands

| Task | Command |
|------|--------|
| Status | `sudo systemctl status tttc-api-staging tttc-web-staging tttc-api-prod tttc-web-prod` |
| Restart | `sudo systemctl restart tttc-api-staging tttc-web-staging` (or `...-prod`) |
| Logs (last) | `sudo journalctl -u tttc-api-staging -n 50` (or `...-prod`) |
| Logs (follow) | `sudo journalctl -u tttc-api-staging -f` |
| Stop | `sudo systemctl stop tttc-api-staging tttc-web-staging` |
| Disable at boot | `sudo systemctl disable tttc-api-staging tttc-web-staging` |

---

## 4. After a deploy

When you run **`.\scripts\deploy-staging.ps1`**, the remote script will:

1. Pull, update API and web files, install deps, build.
2. Restart the right units (when allowed by sudoers):
   - `sudo systemctl restart tttc-api-staging tttc-web-staging`
   - `sudo systemctl restart tttc-api-prod tttc-web-prod`

No more pkill + nohup. If you haven’t set up systemd yet, the deploy script still uses nohup (see script logic).
