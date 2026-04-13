import { RISK_COLORS, RISK_LABELS_ZH } from '../utils/constants'

export default function RiskBadge({ labels = [] }) {
  if (!labels || labels.length === 0) return null
  return (
    <div className="flex flex-wrap gap-2">
      {labels.map(label => {
        const colors = RISK_COLORS[label] || RISK_COLORS['Stable']
        return (
          <span
            key={label}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${colors.bg} ${colors.border} ${colors.text}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
            {RISK_LABELS_ZH[label] || label}
          </span>
        )
      })}
    </div>
  )
}
