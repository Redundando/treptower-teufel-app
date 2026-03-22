# Caddy on staging (HTTPS)

**Goal:** Put staging behind Caddy so you get HTTPS on `staging-app.treptower-teufel.de` (frontend) and `staging-api.treptower-teufel.de` (API). Caddy gets certificates from Let’s Encrypt automatically.

**Prerequisite:** DNS for `staging-app` and `staging-api` (A records → `46.225.208.231`). Ports 80 and 443 open (UFW).  
If your domain is not `treptower-teufel.de`, replace it in the Caddyfile and in this doc.

---

## 1. Install Caddy (on the server)

SSH in, then:

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

Check:

```bash
caddy version
```

---

## 2. Caddyfile (config)

Create the config. Replace `treptower-teufel.de` if your domain is different.

```bash
sudo nano /etc/caddy/Caddyfile
```

**Paste this (then fix the domain if needed):**

```caddyfile
# Staging frontend — SPA + /api proxied to API (prefix stripped so backend gets /health not /api/health)
staging-app.treptower-teufel.de {
	handle_path /api/* {
		reverse_proxy localhost:8000
	}
	reverse_proxy localhost:5173
}

# Staging API — direct access (e.g. for scripts or docs)
staging-api.treptower-teufel.de {
	reverse_proxy localhost:8000
}
```

- **staging-app:** Requests to `/api/*` are sent to the API with the `/api` prefix stripped (e.g. `/api/health` → backend sees `/health`). Everything else → frontend (port 5173).
- **staging-api:** For calling the API by hostname (e.g. `https://staging-api.treptower-teufel.de/health`).

Save and exit (Ctrl+O, Enter, Ctrl+X).

---

## 3. Validate and reload Caddy

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

If Caddy wasn’t running yet:

```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

Check status:

```bash
sudo systemctl status caddy
```

---

## 4. Certificates (automatic)

On first request to each hostname, Caddy will ask Let’s Encrypt for a certificate. Port **80** must be reachable from the internet (you already allow it in UFW). No extra steps.

Test in the browser:

- **https://staging-app.treptower-teufel.de** → frontend (hello world)
- **https://staging-api.treptower-teufel.de/health** → `{"status":"ok"}`

If you see a certificate error, wait a minute for DNS to propagate everywhere, or check that 80/443 are open: `sudo ufw status`.

---

## 5. (Optional) Close direct access to 8000 and 5173

So only Caddy is used:

```bash
sudo ufw delete allow 8000/tcp
sudo ufw delete allow 5173/tcp
sudo ufw status
```

API and frontend are then only reachable via Caddy (HTTPS). The deploy script still works because it starts the processes on localhost; Caddy proxies to them.

---

## 6. Frontend: use the right API base

The SPA currently calls `/api/health` (relative). When you open **https://staging-app.treptower-teufel.de**, the browser is on that origin, so `/api/health` goes to the same host and Caddy proxies it to the API. **No change needed** for staging-app.

If you later open the API directly at **staging-api.treptower-teufel.de**, that’s a different origin; CORS might matter for browser calls. For “hello world” and staging-app as the main entry, you’re fine.

---

## 7. Summary (staging)

| URL | Serves |
|-----|--------|
| https://staging-app.treptower-teufel.de | Frontend (Vite preview on 5173); `/api/*` → API (8000) |
| https://staging-api.treptower-teufel.de | API only (8000) |

---

## 8. Production hosts (add when prod stack exists)

Prod uses **different localhost ports** ([server-layout.md](./server-layout.md)): API **8001**, web **5174**.

Append to the same **Caddyfile** (after staging blocks):

```caddyfile
app.treptower-teufel.de {
	handle_path /api/* {
		reverse_proxy localhost:8001
	}
	reverse_proxy localhost:5174
}

api.treptower-teufel.de {
	reverse_proxy localhost:8001
}
```

Then `caddy validate` and `systemctl reload caddy`.

### 8.1 X-Robots-Tag (optional, step 3)

The web app also sets `<meta name="robots" content="noindex, nofollow">` and serves **`/robots.txt`** (`Disallow: /`). To add an HTTP header on **every response** from Caddy (including the API hostnames), put this **inside each site block** you care about (`staging-app`, `staging-api`, `app`, `api`, …):

```caddyfile
	header X-Robots-Tag "noindex, nofollow"
```

Example — staging app:

```caddyfile
staging-app.treptower-teufel.de {
	header X-Robots-Tag "noindex, nofollow"
	handle_path /api/* {
		reverse_proxy localhost:8000
	}
	reverse_proxy localhost:5173
}
```

After editing **`/etc/caddy/Caddyfile`**:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Verify: `curl -sI https://app.treptower-teufel.de/ | grep -i x-robots`

---

## 9. Caddy service

**systemd** `caddy`, config **/etc/caddy/Caddyfile**. After edits: `sudo caddy validate --config /etc/caddy/Caddyfile` then `sudo systemctl reload caddy`.
