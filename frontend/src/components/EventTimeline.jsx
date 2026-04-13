import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../utils/constants'
import { formatDateFull } from '../utils/formatters'

export default function EventTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center text-slate-500 text-sm">
        近期无相关市场事件
      </div>
    )
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <p className="text-slate-400 text-xs mb-4 font-medium uppercase tracking-wide">市场事件时间线</p>
      <div className="space-y-0">
        {events.map((event, idx) => {
          const colors = EVENT_TYPE_COLORS[event.event_type] || EVENT_TYPE_COLORS.game_update
          const isLast = idx === events.length - 1
          return (
            <div key={event.id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div className={`w-3 h-3 rounded-full mt-0.5 flex-shrink-0 ${colors.dot}`} />
                {!isLast && <div className="w-0.5 bg-slate-700 flex-1 my-1" />}
              </div>
              <div className={`mb-4 flex-1 rounded-lg border px-3 py-2.5 ${colors.bg}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-medium ${colors.text}`}>
                    {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
                  </span>
                  <span className="text-slate-500 text-xs">{formatDateFull(event.event_date)}</span>
                </div>
                <p className="text-sm font-semibold text-white">{event.title}</p>
                {event.summary && (
                  <p className="text-slate-400 text-xs mt-1 leading-relaxed">{event.summary}</p>
                )}
                {event.tags && event.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {event.tags.map(tag => (
                      <span key={tag} className="text-xs bg-slate-700/60 text-slate-400 px-1.5 py-0.5 rounded">
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
    </div>
  )
}
