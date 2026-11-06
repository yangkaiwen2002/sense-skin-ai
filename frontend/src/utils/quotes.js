const KINDS = {
  observed: { label: '采集报价', tone: 'observed' },
  demo: { label: '演示数据', tone: 'demo' },
}

export function quoteMetadata(quote, now = Date.now()) {
  const kind = KINDS[quote?.price_kind] || { label: '来源未核验', tone: 'unknown' }
  const stamp = quote?.snapshot_time
  const date = typeof stamp === 'string'
    ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(stamp) ? stamp : `${stamp}Z`) : null
  const validDate = date && Number.isFinite(date.getTime()) ? date : null
  return {
    ...kind,
    date: validDate,
    stale: Boolean(quote?.is_stale || (validDate && now - validDate.getTime() > 86400000)),
  }
}
