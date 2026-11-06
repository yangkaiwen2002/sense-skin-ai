import { quoteMetadata } from '../utils/quotes'

export default function QuoteSource({ quote, compact = false }) {
  if (!quote) return null
  const { label, tone, date, stale } = quoteMetadata(quote)
  const fullDate = date?.toLocaleString('zh-CN', { hour12: false })
  const shortDate = date?.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
  return (
    <div className={`quote-source ${compact ? 'quote-source-compact' : ''}`}>
      <span className={`source-badge source-${tone}`}>{label}</span>
      {stale && <span className="source-badge source-stale">已过期</span>}
      <span className="quote-time" title={fullDate ? `采集时间：${fullDate}` : '采集时间未知'}>
        {!compact && date && '采集于 '}
        {date ? <time dateTime={date.toISOString()}>{compact ? shortDate : fullDate}</time> : '时间未知'}
      </span>
    </div>
  )
}
