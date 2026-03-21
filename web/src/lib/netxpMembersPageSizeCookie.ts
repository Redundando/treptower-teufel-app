export const NETXP_MEMBERS_PAGE_SIZE_COOKIE = 'tt_netxp_members_page_size'

export const NETXP_PAGE_SIZE_OPTIONS = [50, 100, 200, 500, 1000] as const
export type NetxpPageSizeOption = (typeof NETXP_PAGE_SIZE_OPTIONS)[number]

export const DEFAULT_NETXP_PAGE_SIZE: NetxpPageSizeOption = 50

const ALLOWED = new Set<number>(NETXP_PAGE_SIZE_OPTIONS)

export function normalizeNetxpPageSize(n: number): NetxpPageSizeOption {
  if (ALLOWED.has(n)) return n as NetxpPageSizeOption
  return DEFAULT_NETXP_PAGE_SIZE
}

function parseIntCookie(raw: string | undefined): number | null {
  if (raw == null || raw === '') return null
  const n = Number.parseInt(raw, 10)
  if (!Number.isFinite(n)) return null
  return n
}

export function readNetxpMembersPageSizeFromCookie(): NetxpPageSizeOption {
  if (typeof document === 'undefined') return DEFAULT_NETXP_PAGE_SIZE
  const parts = document.cookie.split(';')
  for (const part of parts) {
    const trimmed = part.trim()
    const eq = trimmed.indexOf('=')
    if (eq < 0) continue
    const k = trimmed.slice(0, eq)
    if (k !== NETXP_MEMBERS_PAGE_SIZE_COOKIE) continue
    const v = trimmed.slice(eq + 1)
    const n = parseIntCookie(decodeURIComponent(v))
    if (n == null) return DEFAULT_NETXP_PAGE_SIZE
    return normalizeNetxpPageSize(n)
  }
  return DEFAULT_NETXP_PAGE_SIZE
}

export function writeNetxpMembersPageSizeToCookie(size: NetxpPageSizeOption): void {
  if (typeof document === 'undefined') return
  const maxAge = 365 * 24 * 60 * 60
  document.cookie = `${NETXP_MEMBERS_PAGE_SIZE_COOKIE}=${encodeURIComponent(String(size))}; Path=/; Max-Age=${maxAge}; SameSite=Lax`
}
