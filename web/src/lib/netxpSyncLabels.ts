import * as m from '../paraglide/messages.js'

const SYNC_STATUS_UI: Record<string, () => string> = {
  'Starting NetXP sync...': () => m.netxp_sync_starting(),
  running: () => m.netxp_sync_status_running(),
  'download + parse done': () => m.netxp_sync_status_download_parse(),
  dry_run: () => m.netxp_sync_status_dry_run(),
  success: () => m.netxp_sync_status_success(),
  failed: () => m.netxp_sync_status_failed(),
}

export function netxpSyncStatusLabel(status: string | null | undefined): string {
  if (status == null || status === '') return ''
  return SYNC_STATUS_UI[status]?.() ?? status
}
