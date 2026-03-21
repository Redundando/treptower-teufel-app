export type NetxpMemberStatsBucketKey =
  | 'b0_9'
  | 'b10_19'
  | 'b20_29'
  | 'b30_39'
  | 'b40_49'
  | 'b50_59'
  | 'b60_69'
  | 'b70_79'
  | 'b80_plus'

export type NetxpMemberStatsMetricId =
  | 'all_current_aktiv_or_passiv'
  | 'no_exit_date'
  | 'aktiv_no_exit'
  | 'leaving_this_year_still_member'
  | 'current_aktiv'
  | 'current_passiv'

/** Column / API metric order; keep in sync with backend `public_stats._METRIC_IDS`. */
export const NETXP_MEMBER_STATS_METRIC_IDS: readonly NetxpMemberStatsMetricId[] = [
  'all_current_aktiv_or_passiv',
  'no_exit_date',
  'aktiv_no_exit',
  'leaving_this_year_still_member',
  'current_aktiv',
  'current_passiv',
]

export type NetxpMemberStatsMetricSlice = {
  total: number
  unknown_age: number
  buckets: number[]
}

export type NetxpMemberStatsResponse = {
  reference_year: number
  age_as_of: string
  bucket_keys: NetxpMemberStatsBucketKey[]
  metrics: Record<NetxpMemberStatsMetricId, NetxpMemberStatsMetricSlice>
}
