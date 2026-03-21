# Data table (shared UI)

Small **presentational** pieces for admin list views. They do **not** fetch data or encode domain rules—that stays in the route or API.

## Pieces

| File | Role |
|------|------|
| `DataTable.svelte` | Renders `<table>` with sortable headers (`aria-sort`), rows, optional row click + selection highlight. You pass `columns`, `rows`, `sortBy` / `sortDir`, `onSort`, `getCell`, `getRowKey`. |
| `ColumnPicker.svelte` | `<details>` + checkboxes for visible columns. Bind `visibleIds` (string[]). |
| `PageSizeSelect.svelte` | “Rows per page” `<select>`. |
| `dataTableColumn.ts` | `DataTableColumnDef`: use `sortable: false` when the API cannot sort; optional `sortKey` if the UI column id differs from `sort_by`. |

## Usage pattern

1. Define column defs (labels, sortability, optional `sortKey`).
2. Load rows via your store/API (server paging recommended for large sets).
3. Compose filters **outside** these components (search, facets, etc.)—see NetXP members route.
4. Persist table chrome (columns, sort, page size) in a **route-specific** cookie or storage—see `lib/netxpViewPrefs.ts` for NetXP.

## Examples in this repo

- Full integration: `routes/admin/netxp-members/AdminNetxpMembersPage.svelte`
- Minimal static table: `routes/AdminCreateUserPage.svelte` (reference roles)

## Expandable panels (`<details>`)

Column picker and similar admin UIs share the same bordered `<details>` shell (summary chevron, body). The Sass mixins live in [`styles/_expandablePanel.scss`](../../styles/_expandablePanel.scss); reuse them when adding another expandable filter or section on admin routes.
