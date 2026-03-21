<script lang="ts">
  import type { DataTableColumnDef } from './dataTableColumn'
  import { columnSortKey } from './dataTableColumn'
  import commonStyles from '../../styles/common.module.scss'
  import styles from './DataTable.module.scss'

  type Props = {
    columns: DataTableColumnDef[]
    rows: unknown[]
    sortBy: string | null
    sortDir: 'asc' | 'desc'
    onSort: (columnId: string) => void
    getCell: (row: unknown, columnId: string) => string
    getRowKey: (row: unknown) => string
    onRowClick?: (row: unknown) => void
    selectedKey?: string | null
  }

  let {
    columns,
    rows,
    sortBy,
    sortDir,
    onSort,
    getCell,
    getRowKey,
    onRowClick,
    selectedKey = null
  }: Props = $props()

  function sortActive(col: DataTableColumnDef): boolean {
    return sortBy === columnSortKey(col)
  }

  function ariaSortFor(col: DataTableColumnDef): 'ascending' | 'descending' | 'none' | undefined {
    if (col.sortable === false) return undefined
    if (!sortActive(col)) return 'none'
    return sortDir === 'asc' ? 'ascending' : 'descending'
  }
</script>

<div class={commonStyles.tableFrame}>
  <table>
    <thead>
      <tr>
        {#each columns as col}
          <th scope="col" aria-sort={ariaSortFor(col)}>
            {#if col.sortable === false}
              <span class={styles.thPlain}>{col.label}</span>
            {:else}
              <button
                type="button"
                class={styles.sortHeader}
                onclick={() => onSort(col.id)}
              >
                <span>{col.label}</span>
                {#if sortActive(col)}
                  <span class={styles.sortCaret} aria-hidden="true">
                    {sortDir === 'asc' ? '↑' : '↓'}
                  </span>
                {/if}
              </button>
            {/if}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each rows as row (getRowKey(row))}
        <tr
          class="{styles.dataRow}{selectedKey != null && selectedKey === getRowKey(row)
            ? ' ' + styles.rowSelected
            : ''}"
          onclick={() => onRowClick?.(row)}
          onkeydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onRowClick?.(row)
            }
          }}
          tabindex={onRowClick ? 0 : undefined}
          aria-selected={selectedKey != null && selectedKey === getRowKey(row) ? 'true' : 'false'}
        >
          {#each columns as col}
            <td>{getCell(row, col.id)}</td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
