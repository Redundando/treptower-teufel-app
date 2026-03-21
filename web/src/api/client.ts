import type { Me, Role } from '../types/auth'
import type { NetxpMember } from '../types/netxpMember'
import {
  NETXP_MEMBER_STATS_METRIC_IDS,
  type NetxpMemberStatsMetricId,
  type NetxpMemberStatsMetricSlice,
  type NetxpMemberStatsResponse,
} from '../types/netxpMemberStats'

async function parseDetail(r: Response): Promise<string | undefined> {
  try {
    const j = (await r.json()) as { detail?: string }
    return j?.detail
  } catch {
    return undefined
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

function emptyMetricSlice(): NetxpMemberStatsMetricSlice {
  return { total: 0, unknown_age: 0, buckets: [0, 0, 0, 0, 0, 0, 0, 0, 0] }
}

/** Fills missing metrics (e.g. older API) so UI never reads undefined buckets. */
function normalizeNetxpMemberStats(raw: NetxpMemberStatsResponse): NetxpMemberStatsResponse {
  const metrics = { ...raw.metrics } as Record<NetxpMemberStatsMetricId, NetxpMemberStatsMetricSlice>
  for (const id of NETXP_MEMBER_STATS_METRIC_IDS) {
    const m = metrics[id]
    if (!m) {
      metrics[id] = emptyMetricSlice()
      continue
    }
    const b = m.buckets ?? []
    metrics[id] = {
      total: m.total ?? 0,
      unknown_age: m.unknown_age ?? 0,
      buckets: Array.from({ length: 9 }, (_, i) => b[i] ?? 0),
    }
  }
  return { ...raw, metrics }
}

export async function fetchNetxpMemberStats(): Promise<NetxpMemberStatsResponse> {
  const r = await fetch('/api/public/netxp-member-stats', { cache: 'no-store' })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Load membership stats failed (${r.status})`)
  }

  const raw = (await r.json()) as NetxpMemberStatsResponse
  const missing = NETXP_MEMBER_STATS_METRIC_IDS.filter(
    (id) => raw.metrics == null || !(id in raw.metrics),
  )
  if (missing.length > 0) {
    console.warn(
      '[netxp-member-stats] API omitted metric key(s); table uses zeros until the server is updated:',
      missing.join(', '),
    )
  }
  return normalizeNetxpMemberStats(raw)
}

export async function fetchNetxpMembers(
  token: string,
  params: {
    page: number
    pageSize: number
    activeOnly: boolean
    search: string
    currentMembersOnly: boolean
    youthOnly: boolean
    csvStatusAktiv?: boolean
    csvStatusPassiv?: boolean
    sortBy?: string | null
    sortDir?: 'asc' | 'desc'
  }
): Promise<{ page: number; page_size: number; total: number; items: NetxpMember[] }> {
  const p = new URLSearchParams()
  p.set('page', String(params.page))
  p.set('page_size', String(params.pageSize))
  p.set('active_only', params.activeOnly ? 'true' : 'false')
  p.set('current_members_only', params.currentMembersOnly ? 'true' : 'false')
  p.set('youth_only', params.youthOnly === true ? 'true' : 'false')
  if (params.csvStatusAktiv === true) p.set('csv_status_aktiv', 'true')
  if (params.csvStatusPassiv === true) p.set('csv_status_passiv', 'true')
  const s = params.search.trim()
  if (s) p.set('search', s)
  if (params.sortBy != null && String(params.sortBy).length > 0) {
    p.set('sort_by', String(params.sortBy))
    p.set('sort_dir', params.sortDir ?? 'asc')
  }

  const r = await fetch(`/api/netxp-members?${p.toString()}`, {
    cache: 'no-store',
    headers: { Authorization: `Bearer ${token}` }
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Load NetXP members failed (${r.status})`)
  }

  return (await r.json()) as {
    page: number
    page_size: number
    total: number
    items: NetxpMember[]
  }
}

/** Query params shared by CSV and Excel NetXP export endpoints. */
export type NetxpMembersExportParams = {
  activeOnly: boolean
  search: string
  currentMembersOnly: boolean
  youthOnly: boolean
  csvStatusAktiv?: boolean
  csvStatusPassiv?: boolean
  /** When set, export only these column ids (same as column picker); order preserved. */
  columns?: string[]
  sortBy?: string | null
  sortDir?: 'asc' | 'desc'
}

function netxpMembersExportSearchParams(params: NetxpMembersExportParams): URLSearchParams {
  const p = new URLSearchParams()
  p.set('active_only', params.activeOnly ? 'true' : 'false')
  p.set('current_members_only', params.currentMembersOnly ? 'true' : 'false')
  p.set('youth_only', params.youthOnly === true ? 'true' : 'false')
  if (params.csvStatusAktiv === true) p.set('csv_status_aktiv', 'true')
  if (params.csvStatusPassiv === true) p.set('csv_status_passiv', 'true')
  const s = params.search.trim()
  if (s) p.set('search', s)
  if (params.sortBy != null && String(params.sortBy).length > 0) {
    p.set('sort_by', String(params.sortBy))
    p.set('sort_dir', params.sortDir ?? 'asc')
  }
  if (params.columns?.length) {
    for (const c of params.columns) {
      p.append('columns', c)
    }
  }
  return p
}

/** CSV export with same filter/sort semantics as the list (no pagination). */
export async function exportNetxpMembersCsv(
  token: string,
  params: NetxpMembersExportParams
): Promise<Blob> {
  const q = netxpMembersExportSearchParams(params)
  const r = await fetch(`/api/netxp-members/export?${q.toString()}`, {
    cache: 'no-store',
    headers: { Authorization: `Bearer ${token}` }
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Export NetXP members failed (${r.status})`)
  }

  return await r.blob()
}

/** Excel export with same filter/sort semantics as the list (no pagination). */
export async function exportNetxpMembersXlsx(
  token: string,
  params: NetxpMembersExportParams
): Promise<Blob> {
  const q = netxpMembersExportSearchParams(params)
  const r = await fetch(`/api/netxp-members/export/xlsx?${q.toString()}`, {
    cache: 'no-store',
    headers: { Authorization: `Bearer ${token}` }
  })

  if (!r.ok) {
    throw new Error((await parseDetail(r)) ?? `Export NetXP members failed (${r.status})`)
  }

  return await r.blob()
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

