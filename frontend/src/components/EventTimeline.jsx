import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../utils/constants'
import { formatDateFull } from '../utils/formatters'
import EmptyState from './ui/EmptyState'
import { CalendarBlank } from '@phosphor-icons/react'

export default function EventTimeline({ events = [] }) {
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
              {!isLast && <div className="w-px flex-1 bg-white/[0.06] my-1" />}
            </div>
            <div className={`rounded-[var(--radius-sm)] border px-3 py-2.5 flex-1 ${colors.bg}`} style={{ marginBottom: isLast ? 0 : 8 }}>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className={`text-xs font-medium ${colors.text}`}>{EVENT_TYPE_LABELS[event.event_type] || event.event_type}</span>
                <span className="text-[11px] text-[var(--text-dim)] shrink-0 font-tabular">{formatDateFull(event.event_date)}</span>
              </div>
              <p className="text-[13px] font-semibold text-[var(--text-primary)]">{event.title}</p>
              {event.summary && <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{event.summary}</p>}
              {event.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {event.tags.map(tag => (
                    <span key={tag} className="text-[10px] bg-white/[0.07] text-[var(--text-dim)] px-1.5 py-0.5 rounded">#{tag}</span>
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
