<script lang="ts">
  import commonStyles from '../../styles/common.module.scss'
  import styles from './PageSizeSelect.module.scss'
  import * as m from '../../paraglide/messages.js'

  type Props = {
    options: readonly number[]
    value: number
    disabled?: boolean
    onChange: (e: Event) => void | Promise<void>
  }

  let { options, value, disabled = false, onChange }: Props = $props()
</script>

<label class={styles.pageSizeField}>
  {m.netxp_rows_per_page()}
  <select
    class={styles.pageSizeSelect}
    {disabled}
    value={String(value)}
    onchange={(e) => void onChange(e)}
  >
    {#each options as n}
      <option value={String(n)}>{n}</option>
    {/each}
  </select>
</label>
