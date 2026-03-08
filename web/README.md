# TTTC Web (Frontend)

Minimal **Vite + Svelte** app for the Treptower Teufel Club. Hello world plus a call to the API `/health` endpoint (proxied to avoid CORS).

## Setup

```powershell
npm install
```

## Run (dev)

```powershell
npm run dev
```

Open http://localhost:5173. The API should be running on port 8000 (or edit `vite.config.ts` proxy target).

## Build

```powershell
npm run build
```

Output in `dist/`. Serve with any static host or via Caddy/nginx on staging.
