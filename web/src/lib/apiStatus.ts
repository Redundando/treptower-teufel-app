import * as m from '../paraglide/messages.js'

/** Maps raw `checkApi()` strings to translated UI text. */
export function formatApiStatusDisplay(raw: string): string {
  if (raw === 'API: offline') return m.api_health_offline()
  const http = /^API: (\d+)$/.exec(raw)
  if (http) return m.api_health_http({ status: http[1] })
  const rest = /^API: (.+)$/.exec(raw)
  if (rest) return m.api_health_ok({ status: rest[1] })
  return raw
}
