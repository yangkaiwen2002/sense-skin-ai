import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../utils/constants'
import { formatDateFull } from '../utils/formatters'

export default function EventTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <p style={{ color: 'var(--text-dim)', fontSize: 13, textAlign: 'center', padding: '12px 0' }}>
        近期无相关市场事件
      </p>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {events.map((event, idx) => {
        const colors = EVENT_TYPE_COLORS[event.event_type] || EVENT_TYPE_COLORS.game_update
        const isLast = idx === events.length - 1
        return (
          <div key={event.id} style={{ display: 'flex', gap: 10 }}>
            {/* Timeline spine */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
              <div className={`w-3 h-3 rounded-full mt-0.5 flex-shrink-0 ${colors.dot}`} style={{ marginTop: 4 }} />
              {!isLast && (
                <div style={{ width: 1, flex: 1, background: 'rgba(255,255,255,0.06)', margin: '4px 0' }} />
              )}
            </div>
            {/* Event card */}
            <div
              className={`rounded-lg border px-3 py-2.5 ${colors.bg}`}
              style={{ flex: 1, marginBottom: isLast ? 0 : 8 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                <span className={`text-xs font-medium ${colors.text}`}>
                  {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{formatDateFull(event.event_date)}</span>
              </div>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>{event.title}</p>
              {event.summary && (
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
                  {event.summary}
                </p>
              )}
              {event.tags && event.tags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                  {event.tags.map(tag => (
                    <span
                      key={tag}
                      style={{ fontSize: 10, background: 'rgba(255,255,255,0.07)', color: 'var(--text-dim)', padding: '2px 6px', borderRadius: 4 }}
                    >
                      #{tag}
                    </span>
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
