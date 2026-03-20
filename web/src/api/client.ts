import type { Me, Role } from '../types/auth'
import type { NetxpMember } from '../types/members'

async function parseDetail(r: Response): Promise<string | undefined> {
  try {
    const j = (await r.json()) as { detail?: string }
    return j?.detail
  } catch {
    return undefined
  }
}

export async function checkApi(): Promise<string> {
  try {
    const r = await fetch('/api/health')
    const j = (await r.json().catch(() => ({}))) as { status?: string }
    return r.ok ? `API: ${j.status ?? 'unknown'}` : `API: ${r.status}`
  } catch {
    return 'API: offline'
  }
}

export async function fetchMe(token: string): Promise<Me> {
  const r = await fetch('/api/auth/me', {
    headers: { Authorization: `Bearer ${token}` }
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Fetch me failed (${r.status})`)
  }

  return (await r.json()) as Me
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const r = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Login failed (${r.status})`)
  }

  return (await r.json()) as { access_token: string }
}

export async function adminCreateUser(
  token: string,
  payload: { email: string; password: string; role: Role }
): Promise<{ email: string; role: Role }> {
  const r = await fetch('/api/auth/admin/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Create user failed (${r.status})`)
  }

  return (await r.json()) as { email: string; role: Role }
}

export async function fetchMembers(
  token: string,
  params: {
    page: number
    pageSize: number
    activeOnly: boolean
    search: string
  }
): Promise<{ page: number; page_size: number; total: number; items: NetxpMember[] }> {
  const p = new URLSearchParams()
  p.set('page', String(params.page))
  p.set('page_size', String(params.pageSize))
  p.set('active_only', params.activeOnly ? 'true' : 'false')
  const s = params.search.trim()
  if (s) p.set('search', s)

  const r = await fetch(`/api/members?${p.toString()}`, {
    headers: { Authorization: `Bearer ${token}` }
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Load members failed (${r.status})`)
  }

  return (await r.json()) as {
    page: number
    page_size: number
    total: number
    items: NetxpMember[]
  }
}

export async function syncNetxpMembers(
  token: string,
): Promise<{ job_id: string }> {
  const r = await fetch('/api/netxp-members/sync', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Start NetXP sync failed (${r.status})`)
  }

  return (await r.json()) as { job_id: string }
}

