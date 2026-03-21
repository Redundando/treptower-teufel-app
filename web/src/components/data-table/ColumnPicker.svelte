<script lang="ts">

  import commonStyles from '../../styles/common.module.scss'

  import styles from './ColumnPicker.module.scss'

  import * as m from '../../paraglide/messages.js'



  type Col = { id: string; label: string }



  type Props = {

    columns: Col[]

    visibleIds: string[]

    summaryHint?: string

    onReset: () => void

  }



  let { columns, visibleIds = $bindable([]), summaryHint, onReset }: Props = $props()

</script>



<details class={styles.columnPanel}>

  <summary class={styles.columnSummary}>{m.netxp_column_picker_summary()}</summary>

  <div class={styles.columnPanelBody}>

    {#if summaryHint}

      <p class={`${commonStyles.muted} ${styles.columnHint}`}>

        {summaryHint}

      </p>

    {/if}

    <div class={styles.columnActions}>

      <button type="button" class={commonStyles.btnSecondary} onclick={onReset}
        >{m.netxp_column_picker_reset()}</button
      >

    </div>

    <div class={styles.columnGrid}>

      {#each columns as col}

        <label>

          <input type="checkbox" bind:group={visibleIds} value={col.id} />

          {col.label}

        </label>

      {/each}

    </div>

  </div>

</details>


