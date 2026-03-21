import {
  DEFAULT_NETXP_PAGE_SIZE,
  NETXP_MEMBERS_PAGE_SIZE_COOKIE,
  normalizeNetxpPageSize,
  type NetxpPageSizeOption
} from './netxpMembersPageSizeCookie'

/** All valid NetXP admin table column ids (must match ColId in AdminNetxpMembersPage). */
export const NETXP_MEMBER_ALL_COL_IDS = new Set<string>([
  'id',
  'netxp_id',
  'active',
  'first_seen_at',
  'last_seen_at',
  'inactive_since',
  'mitgliedsnummer',
  'vorname',
  'nachname',
  'geburtsdatum',
  'age',
  'eintrittsdatum',
  'member_years',
  'austrittsdatum',
  'mitgliedsart',
  'strasse',
  'plz',
  'ort',
  'telefon_privat',
  'telefon_arbeit',
  'email_privat',
  'nx_ssp_registration_code',
  'beitragsnamen',
  'info',
  'csv_status'
])

export const NETXP_VIEW_PREFS_COOKIE = 'tt_netxp_members_view_v1'
const LEGACY_COL_STORAGE_KEY = 'tttc-admin-netxp-member-cols-v3'

/** Keep payload under typical 4KB cookie limits. */
const MAX_SEARCH_LEN = 200

export type NetxpViewPrefsV1 = {
  v: 1
  pageSize: NetxpPageSizeOption
  cols: string[]
  sortBy: string | null
  sortDir: 'asc' | 'desc'
  search: string
  activeOnly: boolean
  currentOnly: boolean
  youthOnly: boolean
  /** Restrict list to NetXP CSV `csv_status` = aktiv (and/or passiv when both set). */
  csvStatusAktiv: boolean
  csvStatusPassiv: boolean
}

const COOKIE_MAX_SAFE = 3500

function readCookieRaw(name: string): string | null {
  if (typeof document === 'undefined') return null
  const parts = document.cookie.split(';')
  for (const part of parts) {
    const trimmed = part.trim()
    const eq = trimmed.indexOf('=')
    if (eq < 0) continue
    const k = trimmed.slice(0, eq)
    if (k !== name) continue
    return decodeURIComponent(trimmed.slice(eq + 1))
  }
  return null
}

function writeCookieRaw(name: string, value: string): void {
  if (typeof document === 'undefined') return
  const maxAge = 365 * 24 * 60 * 60
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`
}

function deleteCookie(name: string): void {
  if (typeof document === 'undefined') return
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`
}

function trimPrefsForSize(p: NetxpViewPrefsV1): NetxpViewPrefsV1 {
  let search = p.search.slice(0, MAX_SEARCH_LEN)
  let cols = p.cols
  let out: NetxpViewPrefsV1 = { ...p, search, cols }
  let encoded = JSON.stringify(out)
  while (encoded.length > COOKIE_MAX_SAFE && search.length > 0) {
    search = search.slice(0, Math.max(0, search.length - 20))
    out = { ...out, search }
    encoded = JSON.stringify(out)
  }
  return out
}

export function readNetxpViewPrefsCookie(): NetxpViewPrefsV1 | null {
  if (typeof document === 'undefined') return null
  const raw = readCookieRaw(NETXP_VIEW_PREFS_COOKIE)
  if (!raw) return null
  try {
    const j = JSON.parse(raw) as Partial<NetxpViewPrefsV1>
    if (j.v !== 1 || !Array.isArray(j.cols)) return null
    return {
      v: 1,
      pageSize: normalizeNetxpPageSize(Number(j.pageSize ?? DEFAULT_NETXP_PAGE_SIZE)),
      cols: j.cols.filter((x) => typeof x === 'string' && NETXP_MEMBER_ALL_COL_IDS.has(x)),
      sortBy: typeof j.sortBy === 'string' ? j.sortBy : null,
      sortDir: j.sortDir === 'desc' ? 'desc' : 'asc',
      search: typeof j.search === 'string' ? j.search.slice(0, MAX_SEARCH_LEN) : '',
      activeOnly: j.activeOnly !== false,
      currentOnly: j.currentOnly !== false,
      youthOnly: j.youthOnly === true,
      csvStatusAktiv: j.csvStatusAktiv === true,
      csvStatusPassiv: j.csvStatusPassiv === true
    }
  } catch {
    return null
  }
}

/** Migrate legacy page-size-only cookie + localStorage column prefs. */
export function loadNetxpViewPrefsWithMigration(): NetxpViewPrefsV1 {
  const fromCookie = readNetxpViewPrefsCookie()
  if (fromCookie) {
    fromCookie.cols = fromCookie.cols.filter((id) => NETXP_MEMBER_ALL_COL_IDS.has(id))
    return fromCookie
  }

  let pageSize = DEFAULT_NETXP_PAGE_SIZE
  const legacyPs = readCookieRaw(NETXP_MEMBERS_PAGE_SIZE_COOKIE)
  if (legacyPs) {
    const n = Number.parseInt(legacyPs, 10)
    if (Number.isFinite(n)) pageSize = normalizeNetxpPageSize(n)
  }

  let cols: string[] = []
  try {
    if (typeof localStorage !== 'undefined') {
      const raw = localStorage.getItem(LEGACY_COL_STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as unknown
        if (Array.isArray(parsed)) {
          cols = parsed.filter((x): x is string => typeof x === 'string' && NETXP_MEMBER_ALL_COL_IDS.has(x))
        }
      }
    }
  } catch {
    /* ignore */
  }

  return {
    v: 1,
    pageSize,
    cols,
    sortBy: null,
    sortDir: 'asc',
    search: '',
    activeOnly: true,
    currentOnly: true,
    youthOnly: false,
    csvStatusAktiv: false,
    csvStatusPassiv: false
  }
}

export function writeNetxpViewPrefsCookie(p: NetxpViewPrefsV1): void {
  const trimmed = trimPrefsForSize(p)
  writeCookieRaw(NETXP_VIEW_PREFS_COOKIE, JSON.stringify(trimmed))
  deleteCookie(NETXP_MEMBERS_PAGE_SIZE_COOKIE)
  try {
    if (typeof localStorage !== 'undefined') localStorage.removeItem(LEGACY_COL_STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export function buildNetxpViewPrefsFromStores(
  get: {
    pageSize: number
    search: string
    activeOnly: boolean
    currentOnly: boolean
    youthOnly: boolean
    csvStatusAktiv: boolean
    csvStatusPassiv: boolean
    sortBy: string | null
    sortDir: 'asc' | 'desc'
  },
  visibleColIds: string[]
): NetxpViewPrefsV1 {
  return {
    v: 1,
    pageSize: normalizeNetxpPageSize(get.pageSize),
    cols: [...visibleColIds],
    sortBy: get.sortBy,
    sortDir: get.sortDir,
    search: get.search.slice(0, MAX_SEARCH_LEN),
    activeOnly: get.activeOnly,
    currentOnly: get.currentOnly,
    youthOnly: get.youthOnly,
    csvStatusAktiv: get.csvStatusAktiv,
    csvStatusPassiv: get.csvStatusPassiv
  }
}
