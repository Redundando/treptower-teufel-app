/** Part before `@` for compact menus; falls back to full string if malformed. */
export function emailLocalPart(email: string): string {
  const at = email.indexOf('@')
  if (at <= 0) return email
  return email.slice(0, at)
}
