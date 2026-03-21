import * as m from '../paraglide/messages.js'

const DETAIL_EXACT: Record<string, () => string> = {
  'Email and password required': () => m.api_err_email_password_required(),
  'Invalid credentials': () => m.api_err_invalid_credentials(),
  'Missing token': () => m.api_err_missing_token(),
  'Invalid token': () => m.api_err_invalid_token(),
  'User not active': () => m.api_err_user_not_active(),
  'Email already exists': () => m.api_err_email_exists(),
  'User creation failed': () => m.api_err_user_creation_failed(),
  'Not authenticated': () => m.api_err_not_authenticated(),
}

type Pat = { re: RegExp; translate: (match: RegExpMatchArray) => string }

const DETAIL_PATTERNS: Pat[] = [
  { re: /^Fetch me failed \((\d+)\)$/, translate: (x) => m.api_err_fetch_me({ status: x[1] }) },
  { re: /^Login failed \((\d+)\)$/, translate: (x) => m.api_err_login({ status: x[1] }) },
  { re: /^Create user failed \((\d+)\)$/, translate: (x) => m.api_err_create_user({ status: x[1] }) },
  { re: /^Load NetXP members failed \((\d+)\)$/, translate: (x) => m.api_err_netxp_load({ status: x[1] }) },
  { re: /^Export NetXP members failed \((\d+)\)$/, translate: (x) => m.api_err_netxp_export({ status: x[1] }) },
  { re: /^Start NetXP sync failed \((\d+)\)$/, translate: (x) => m.api_err_netxp_sync({ status: x[1] }) },
  {
    re: /^Load membership stats failed \((\d+)\)$/,
    translate: (x) => m.api_err_netxp_stats({ status: x[1] }),
  },
  { re: /^Sync stream failed \((\d+)\)$/, translate: (x) => m.api_err_sync_stream({ status: x[1] }) },
]

/** Translates API `detail` strings and client `Error.message` patterns from `api/client.ts`. */
export function translateClientErrorMessage(message: string): string {
  const t = message.trim()
  const exact = DETAIL_EXACT[t]
  if (exact) return exact()
  for (const p of DETAIL_PATTERNS) {
    const match = p.re.exec(t)
    if (match) return p.translate(match)
  }
  if (t === 'Network error') return m.api_err_network()
  if (t === 'Missing SSE response body') return m.api_err_sync_missing_body()
  return m.api_err_generic({ message })
}
