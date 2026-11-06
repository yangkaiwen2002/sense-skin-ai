import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../utils/constants'
import { formatDateFull } from '../utils/formatters'
import EmptyState from './ui/EmptyState'
import { CalendarBlank } from '@phosphor-icons/react'

export default function EventTimeline({ events = [], compact = false }) {
  if (!events.length) {
    return <EmptyState icon={CalendarBlank} sub="近期无相关市场事件" />
  }

  return (
    <div className="flex flex-col">
      {events.map((event, idx) => {
        const colors = EVENT_TYPE_COLORS[event.event_type] || EVENT_TYPE_COLORS.game_update
        const isLast = idx === events.length - 1
        return (
          <div key={event.id} className="flex gap-2.5">
            <div className="flex flex-col items-center shrink-0">
              <div className={`w-3 h-3 rounded-full mt-1 shrink-0 ${colors.dot}`} />
              {!isLast && <div className="w-px flex-1 bg-[var(--bg-surface-raised)] my-1" />}
            </div>
            <div className={`rounded-[var(--radius-sm)] border px-3 py-2.5 flex-1 min-w-0 break-words ${colors.bg}`} style={{ marginBottom: isLast ? 0 : 8 }}>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className={`text-xs font-medium ${colors.text}`}>{event.event_type === 'official_news' ? '官方公告 · 影响待评估' : EVENT_TYPE_LABELS[event.event_type] || event.event_type}</span>
                <span className="text-[11px] text-[var(--text-dim)] shrink-0 font-tabular">{formatDateFull(event.event_date)}</span>
              </div>
              <p className="text-[13px] font-semibold text-[var(--text-primary)]">{event.title}</p>
              {event.summary && <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{compact && event.summary.length > 220 ? `${event.summary.slice(0, 220)}…` : event.summary}</p>}
              {event.source_url && /^https:\/\//.test(event.source_url) && (
                <a href={event.source_url} target="_blank" rel="noreferrer" className="text-xs text-[var(--accent)] mt-2 inline-block">查看官方原文 ↗</a>
              )}
              {event.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {event.tags.map(tag => (
                    <span key={tag} className="text-[10px] bg-[var(--bg-surface-raised)] text-[var(--text-dim)] px-1.5 py-0.5 rounded">#{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
