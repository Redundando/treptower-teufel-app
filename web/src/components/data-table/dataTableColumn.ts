/**
 * Contract for server-paged admin tables:
 * - `sortKey` is the value sent to the API as `sort_by` (or equivalent). It must match
 *   backend allowlists (see e.g. `_netxp_members_order_sql` and `_NETXP_MEMBER_SORTABLE_DB`).
 * - `sortable: false` for display-only columns with no server ordering (or client-only derivations
 *   without a backend alias).
 */
export type DataTableColumnDef = {
  id: string
  label: string
  /** When false, header is not a sort control. Default true. */
  sortable?: boolean
  /**
   * API sort field; defaults to `id` when sortable. Use when the UI column id differs from `sort_by`
   * (rare for NetXP; column id matches API).
   */
  sortKey?: string
}

export function columnSortKey(c: DataTableColumnDef): string {
  return c.sortKey ?? c.id
}
