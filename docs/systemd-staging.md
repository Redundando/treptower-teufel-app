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

**Copy the unit files**

```bash
sudo cp /srv/tttc/app/repo/ops/systemd/tttc-api.service /etc/systemd/system/
sudo cp /srv/tttc/app/repo/ops/systemd/tttc-web.service /etc/systemd/system/
sudo systemctl daemon-reload
```

**Enable and start**

```bash
sudo systemctl enable tttc-api tttc-web
sudo systemctl start tttc-api tttc-web
sudo systemctl status tttc-api tttc-web
```

**Check**

- API: `curl -s http://localhost:8000/health` → `{"status":"ok"}`
- Frontend: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5173` → 200

After this, the **deploy script** will restart these services instead of starting processes with nohup.

---

## 3. Useful commands

| Task | Command |
|------|--------|
| Status | `sudo systemctl status tttc-api` / `tttc-web` |
| Restart | `sudo systemctl restart tttc-api` / `tttc-web` |
| Logs (last) | `sudo journalctl -u tttc-api -n 50` (same for `tttc-web`) |
| Logs (follow) | `sudo journalctl -u tttc-api -f` |
| Stop | `sudo systemctl stop tttc-api` / `tttc-web` |
| Disable at boot | `sudo systemctl disable tttc-api` / `tttc-web` |

---

## 4. After a deploy

When you run **`.\scripts\deploy-staging.ps1`**, the remote script will:

1. Pull, update API and web files, install deps, build.
2. Run **`sudo systemctl restart tttc-api tttc-web`** (if the units are installed).

No more pkill + nohup. If you haven’t set up systemd yet, the deploy script still uses nohup (see script logic).
