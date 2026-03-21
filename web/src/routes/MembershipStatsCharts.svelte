<script lang="ts">
  import * as echarts from 'echarts'
  import * as m from '../paraglide/messages.js'
  import type {
    NetxpMemberStatsBucketKey,
    NetxpMemberStatsResponse,
  } from '../types/netxpMemberStats'
  import styles from './MembershipStatsCharts.module.scss'

  type Props = {
    data: NetxpMemberStatsResponse
  }

  let { data }: Props = $props()

  let barTab = $state<'all' | 'aktiv'>('all')

  let barHostRef: HTMLDivElement | undefined = $state()
  let pie1HostRef: HTMLDivElement | undefined = $state()
  let pie2HostRef: HTMLDivElement | undefined = $state()

  /** Narrow layout: avoid outside labels overlapping the legend (see pie options below). */
  let compactPies = $state(
    typeof window !== 'undefined' && window.matchMedia('(max-width: 720px)').matches,
  )

  const colorBrand = '#b51a2c'
  const colorMuted = '#6b6b6b'
  const colorLeaving = '#c45c2a'
  const colorNoExit = '#2d6126'

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

  $effect(() => {
    if (!barHostRef || !data) return
    const chart = echarts.init(barHostRef)
    const metric = barTab === 'all' ? 'all_current_aktiv_or_passiv' : 'current_aktiv'
    const slice = data.metrics[metric]
    const categories = [...data.bucket_keys.map(bucketLabel), m.stats_age_unknown()]
    const values = [...slice.buckets, slice.unknown_age]
    chart.setOption(
      {
        color: [colorBrand],
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 52, right: 20, bottom: 28, top: 16 },
        xAxis: {
          type: 'category',
          data: categories,
          axisLabel: { interval: 0, rotate: 32, fontSize: 11 },
        },
        yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [
          {
            type: 'bar',
            data: values,
            barMaxWidth: 36,
            itemStyle: { borderRadius: [2, 2, 0, 0] },
          },
        ],
      },
      true,
    )
    const ro = new ResizeObserver(() => chart.resize())
    ro.observe(barHostRef)
    return () => {
      ro.disconnect()
      chart.dispose()
    }
  })

  $effect(() => {
    if (typeof window === 'undefined') return
    const mq = window.matchMedia('(max-width: 720px)')
    const sync = () => {
      compactPies = mq.matches
    }
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  })

  $effect(() => {
    if (!pie1HostRef || !pie2HostRef || !data) return
    const c1 = echarts.init(pie1HostRef)
    const c2 = echarts.init(pie2HostRef)
    const aktiv = data.metrics.current_aktiv.total
    const passiv = data.metrics.current_passiv.total
    const leaving = data.metrics.leaving_this_year_still_member.total
    const allCurrent = data.metrics.all_current_aktiv_or_passiv.total
    const notLeavingThisYear = Math.max(0, allCurrent - leaving)

    const name1a = m.stats_metric_current_aktiv()
    const name1b = m.stats_metric_current_passiv()
    const name2a = m.stats_metric_leaving_year({ year: String(data.reference_year) })
    const name2b = m.stats_pie_not_leaving_this_year()

    const pieLabelWide = { formatter: '{b}\n{c} ({d}%)', fontSize: 12 }
    const legendFormatter =
      (pairs: [string, number][]) =>
      (legendName: string) => {
        const hit = pairs.find(([n]) => n === legendName)
        return hit != null ? `${legendName}: ${hit[1]}` : legendName
      }

    const legendCompact = {
      top: 8,
      left: 'center' as const,
      orient: 'vertical' as const,
      itemGap: 8,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 11 },
    }
    const legendWide = { bottom: 0, left: 'center' as const }

    const seriesCompact = {
      radius: ['26%', '50%'] as [string, string],
      center: ['50%', '58%'] as [string, string],
      avoidLabelOverlap: true,
      label: { show: false },
      labelLine: { show: false },
      emphasis: { label: { show: false }, scale: true },
    }
    const seriesWide = {
      radius: ['38%', '68%'] as [string, string],
      center: ['50%', '46%'] as [string, string],
      avoidLabelOverlap: true,
      label: pieLabelWide,
      emphasis: { label: { show: true, fontWeight: 'bold' } },
    }

    c1.setOption(
      {
        color: [colorBrand, colorMuted],
        tooltip: { trigger: 'item' },
        legend: compactPies
          ? {
              ...legendCompact,
              formatter: legendFormatter([
                [name1a, aktiv],
                [name1b, passiv],
              ]),
            }
          : legendWide,
        series: [
          {
            type: 'pie',
            ...(compactPies ? seriesCompact : seriesWide),
            data: [
              { value: aktiv, name: name1a },
              { value: passiv, name: name1b },
            ],
          },
        ],
      },
      true,
    )

    c2.setOption(
      {
        color: [colorLeaving, colorNoExit],
        tooltip: { trigger: 'item' },
        legend: compactPies
          ? {
              ...legendCompact,
              formatter: legendFormatter([
                [name2a, leaving],
                [name2b, notLeavingThisYear],
              ]),
            }
          : legendWide,
        series: [
          {
            type: 'pie',
            ...(compactPies ? seriesCompact : seriesWide),
            minShowLabelAngle: 1,
            data: [
              { value: leaving, name: name2a },
              { value: notLeavingThisYear, name: name2b },
            ],
          },
        ],
      },
      true,
    )

    const ro1 = new ResizeObserver(() => c1.resize())
    const ro2 = new ResizeObserver(() => c2.resize())
    ro1.observe(pie1HostRef)
    ro2.observe(pie2HostRef)
    return () => {
      ro1.disconnect()
      ro2.disconnect()
      c1.dispose()
      c2.dispose()
    }
  })
</script>

<section class={styles.chartsSection} aria-label={m.stats_charts_section_aria()}>
  <h3 class={styles.chartsHeading}>{m.stats_charts_bar_heading()}</h3>

  <div class={styles.tabRow} role="tablist" aria-label={m.stats_charts_bar_tabs_aria()}>
    <button
      type="button"
      role="tab"
      class={styles.tab}
      aria-selected={barTab === 'all'}
      tabindex={barTab === 'all' ? 0 : -1}
      onclick={() => (barTab = 'all')}
    >
      {m.stats_chart_tab_all()}
    </button>
    <button
      type="button"
      role="tab"
      class={styles.tab}
      aria-selected={barTab === 'aktiv'}
      tabindex={barTab === 'aktiv' ? 0 : -1}
      onclick={() => (barTab = 'aktiv')}
    >
      {m.stats_chart_tab_aktiv_netxp()}
    </button>
  </div>

  <div
    bind:this={barHostRef}
    class={styles.chartHost}
    role="tabpanel"
    aria-label={barTab === 'all' ? m.stats_chart_tab_all() : m.stats_chart_tab_aktiv_netxp()}
  ></div>

  <h3 class={styles.chartsHeading}>{m.stats_charts_pies_heading()}</h3>
  <div class={styles.pieRow}>
    <div class={styles.pieBlock}>
      <p class={styles.pieCaption}>{m.stats_chart_pie_aktiv_passiv_title()}</p>
      <div bind:this={pie1HostRef} class={styles.pieHost}></div>
    </div>
    <div class={styles.pieBlock}>
      <p class={styles.pieCaption}>{m.stats_chart_pie_leaving_title()}</p>
      <div bind:this={pie2HostRef} class={styles.pieHost}></div>
    </div>
  </div>
</section>
