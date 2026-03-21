<script lang="ts">
  import {
    netxpMembersActiveOnly,
    netxpMembersLoading,
    netxpMembersSearch,
    netxpMembersCurrentOnly,
    netxpMembersYouthOnly,
    netxpMembersCsvStatusAktiv,
    netxpMembersCsvStatusPassiv
  } from '../../../stores/netxpMembers'
  import commonStyles from '../../../styles/common.module.scss'
  import pageStyles from './AdminNetxpMembersPage.module.scss'
  import * as m from '../../../paraglide/messages.js'

  type Props = {
    onSearch: () => void | Promise<void>
    onRefresh: () => void | Promise<void>
    onYouthChange: (youthOnly: boolean) => void | Promise<void>
  }

  let { onSearch, onRefresh, onYouthChange }: Props = $props()
</script>

<details class={pageStyles.filterPanel}>
  <summary class={pageStyles.filterPanelSummary}>{m.netxp_filter_summary()}</summary>
  <div class={pageStyles.filterPanelBody}>
    <div class={pageStyles.filterGrid}>
      <label class={pageStyles.filterField}>
        <span class={pageStyles.filterLabel}>{m.netxp_filter_search()}</span>
        <input
          class={pageStyles.filterInput}
          bind:value={$netxpMembersSearch}
          type="text"
          placeholder={m.netxp_filter_search_placeholder()}
          autocomplete="off"
        />
      </label>
      <div class={pageStyles.filterToggles}>
        <label class={pageStyles.filterToggle}>
          <input
            type="checkbox"
            checked={$netxpMembersActiveOnly}
            onchange={(e) => netxpMembersActiveOnly.set(e.currentTarget.checked)}
          />
          <span>{m.netxp_filter_active_only()}</span>
        </label>
        <label class={pageStyles.filterToggle}>
          <input
            type="checkbox"
            checked={$netxpMembersCurrentOnly}
            onchange={(e) => netxpMembersCurrentOnly.set(e.currentTarget.checked)}
          />
          <span>{m.netxp_filter_current_members()}</span>
        </label>
        <label class={pageStyles.filterToggle}>
          <input
            type="checkbox"
            checked={$netxpMembersYouthOnly}
            onchange={async (e) => {
              const v = e.currentTarget.checked
              netxpMembersYouthOnly.set(v)
              await onYouthChange(v)
            }}
          />
          <span>{m.netxp_filter_youth()}</span>
        </label>
        <label class={pageStyles.filterToggle}>
          <input
            type="checkbox"
            checked={$netxpMembersCsvStatusAktiv}
            onchange={(e) => netxpMembersCsvStatusAktiv.set(e.currentTarget.checked)}
          />
          <span>{m.netxp_filter_csv_status_aktiv()}</span>
        </label>
        <label class={pageStyles.filterToggle}>
          <input
            type="checkbox"
            checked={$netxpMembersCsvStatusPassiv}
            onchange={(e) => netxpMembersCsvStatusPassiv.set(e.currentTarget.checked)}
          />
          <span>{m.netxp_filter_csv_status_passiv()}</span>
        </label>
      </div>
    </div>
    <p class={pageStyles.filterNote}>
      {m.netxp_filter_note()}
    </p>
    <p class={pageStyles.filterNote}>
      {m.netxp_filter_csv_status_note()}
    </p>
    <div class={pageStyles.filterActions}>
      <button class={commonStyles.btnPrimary} disabled={$netxpMembersLoading} onclick={onSearch}>
        {m.netxp_filter_search_btn()}
      </button>
      <button class={commonStyles.btnSecondary} disabled={$netxpMembersLoading} onclick={onRefresh}>
        {m.netxp_filter_refresh_btn()}
      </button>
    </div>
  </div>
</details>
