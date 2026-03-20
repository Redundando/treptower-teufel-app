# Auth v1 (JWT + RBAC)

This backend supports user login with email + password and role-based access control:

- `member`: regular authenticated user
- `admin`: can create other users

Tokens are JWT `Bearer` access tokens stored client-side (frontend uses `localStorage`).

## 1) Configuration

1. Ensure `DATABASE_URL` is set in the root `.env` (already required for DB + migrations).
2. Set JWT configuration in the root `.env` (copy from `.env.example`):
   - `JWT_SECRET_KEY`
   - `JWT_ACCESS_TOKEN_SECONDS` (optional, default `86400`)
   - `JWT_ALGORITHM` (optional, default `HS256`)

## 2) Apply migrations

Run DB migrations (creates `app_users`):

```powershell
cd api
python -m app.db.migrate
```

## 3) Seed the initial admin user (one-time)

Because user creation is admin-only, bootstrap the very first admin:

```powershell
cd api
python -m app.auth.seed_admin --email admin@example.com --password 'change-me'
```

This command refuses to run if *any* user already exists.

## 4) Endpoints

### Login

`POST /api/auth/login`

Request body:

```json
{ "email": "admin@example.com", "password": "change-me" }
```

Response:

- `access_token`
- `token_type` (Bearer)
- `user` (`id`, `email`, `role`)

### Current user

`GET /api/auth/me`

Header:

- `Authorization: Bearer <access_token>`

Response:

- `id`, `email`, `role`

### Admin: create user

`POST /api/auth/admin/users`

Header:

- `Authorization: Bearer <admin_access_token>`

Request body:

```json
{ "email": "someone@example.com", "password": "new-password", "role": "member" }
```

## 5) Frontend behavior

The current `web/src/App.svelte`:

- calls `/api/auth/login` to sign in
- stores `access_token` in `localStorage`
- calls `/api/auth/me` to load role
- shows the admin “Create user” form only when role is `admin`

