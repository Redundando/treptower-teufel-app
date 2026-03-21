<script lang="ts">
  import { onMount } from 'svelte'
  import { Link } from 'svelte-navigator'
  import { fetchNetxpMemberStats } from '../api/client'
  import commonStyles from '../styles/common.module.scss'
  import * as m from '../paraglide/messages.js'
  import { translateClientErrorMessage } from '../lib/apiErrorMessage'
  import type {
    NetxpMemberStatsBucketKey,
    NetxpMemberStatsMetricId,
    NetxpMemberStatsResponse,
  } from '../types/netxpMemberStats'
  import { NETXP_MEMBER_STATS_METRIC_IDS } from '../types/netxpMemberStats'
  import styles from './MembershipStatsPage.module.scss'

  let loading = $state(true)
  let error = $state<string | null>(null)
  let data = $state<NetxpMemberStatsResponse | null>(null)

  function metricHeader(id: NetxpMemberStatsMetricId, refYear: number): string {
    switch (id) {
      case 'all_current_aktiv_or_passiv':
        return m.stats_metric_all_current()
      case 'no_exit_date':
        return m.stats_metric_no_exit()
      case 'aktiv_no_exit':
        return m.stats_metric_aktiv_no_exit()
      case 'leaving_this_year_still_member':
        return m.stats_metric_leaving_year({ year: String(refYear) })
      case 'current_aktiv':
        return m.stats_metric_current_aktiv()
      case 'current_passiv':
        return m.stats_metric_current_passiv()
      default:
        return id
    }
  }

  function bucketLabel(key: NetxpMemberStatsBucketKey): string {
    switch (key) {
      case 'b0_9':
        return m.stats_age_bucket_b0_9()
      case 'b10_19':
        return m.stats_age_bucket_b10_19()
      case 'b20_29':
        return m.stats_age_bucket_b20_29()
      case 'b30_39':
        return m.stats_age_bucket_b30_39()
      case 'b40_49':
        return m.stats_age_bucket_b40_49()
      case 'b50_59':
        return m.stats_age_bucket_b50_59()
      case 'b60_69':
        return m.stats_age_bucket_b60_69()
      case 'b70_79':
        return m.stats_age_bucket_b70_79()
      case 'b80_plus':
        return m.stats_age_bucket_b80_plus()
      default:
        return key
    }
  }

  onMount(() => {
    void (async () => {
      loading = true
      error = null
      try {
        data = await fetchNetxpMemberStats()
      } catch (e) {
        error = translateClientErrorMessage(e instanceof Error ? e.message : m.api_err_network())
      } finally {
        loading = false
      }
    })()
  })
</script>

<section class={commonStyles.card}>
  <h2>{m.stats_membership_title()}</h2>
  <p class={commonStyles.muted}>{m.stats_membership_intro()}</p>

  {#if loading}
    <p class={commonStyles.muted}>{m.common_loading()}</p>
  {:else if error}
    <p class={styles.error} role="alert">{error}</p>
    <div class={commonStyles.row}>
      <Link class={commonStyles.btnSecondary} to="/">{m.common_back_to_index()}</Link>
    </div>
  {:else if data}
    <p class={`${commonStyles.muted} ${styles.footnote}`}>
      {m.stats_footnote_age({ year: String(data.reference_year), iso: data.age_as_of })}
    </p>

    {#await import('./MembershipStatsCharts.svelte') then { default: StatsCharts }}
      <StatsCharts {data} />
    {/await}

    <div class={styles.tableWrap}>
      <table class={styles.table}>
        <thead>
          <tr>
            <th scope="col">{m.stats_col_age_group()}</th>
            {#each NETXP_MEMBER_STATS_METRIC_IDS as mid (mid)}
              <th scope="col" class={styles.numHead}>{metricHeader(mid, data.reference_year)}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each data.bucket_keys as bk, i (bk)}
            <tr>
              <th scope="row">{bucketLabel(bk)}</th>
              {#each NETXP_MEMBER_STATS_METRIC_IDS as mid (mid)}
                <td class={styles.numCell}>{data.metrics[mid]?.buckets[i] ?? 0}</td>
              {/each}
            </tr>
          {/each}
          <tr class={styles.subtotalRow}>
            <th scope="row">{m.stats_age_unknown()}</th>
            {#each NETXP_MEMBER_STATS_METRIC_IDS as mid (mid)}
              <td class={styles.numCell}>{data.metrics[mid]?.unknown_age ?? 0}</td>
            {/each}
          </tr>
          <tr class={styles.totalRow}>
            <th scope="row">{m.stats_row_total()}</th>
            {#each NETXP_MEMBER_STATS_METRIC_IDS as mid (mid)}
              <td class={styles.numCell}>{data.metrics[mid]?.total ?? 0}</td>
            {/each}
          </tr>
        </tbody>
      </table>
    </div>

    <div class={commonStyles.row}>
      <Link class={commonStyles.btnSecondary} to="/">{m.common_back_to_index()}</Link>
    </div>
  {/if}
</section>
