/** Client-side auth token persistence (matches API JWT lifetime). */
export const AUTH_TOKEN_COOKIE = 'tt_access_token'

/** 30 days — keep in sync with `api/app/config/app.toml` [jwt] access_token_seconds */
export const AUTH_TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60

function secureCookieSuffix(): string {
  if (typeof location === 'undefined') return ''
  return location.protocol === 'https:' ? '; Secure' : ''
}

export function readAuthTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null
  for (const part of document.cookie.split(';')) {
    const trimmed = part.trim()
    const eq = trimmed.indexOf('=')
    if (eq < 0) continue
    if (trimmed.slice(0, eq) !== AUTH_TOKEN_COOKIE) continue
    const raw = trimmed.slice(eq + 1)
    try {
      return decodeURIComponent(raw)
    } catch {
      return null
    }
  }
  return null
}

export function writeAuthTokenToCookie(token: string): void {
  if (typeof document === 'undefined') return
  document.cookie = `${AUTH_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; Max-Age=${AUTH_TOKEN_MAX_AGE_SECONDS}; SameSite=Lax${secureCookieSuffix()}`
}

export function clearAuthTokenCookie(): void {
  if (typeof document === 'undefined') return
  document.cookie = `${AUTH_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax${secureCookieSuffix()}`
}
