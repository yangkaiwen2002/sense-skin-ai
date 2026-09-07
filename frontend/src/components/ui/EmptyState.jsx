export default function EmptyState({ icon: Icon, title, sub, action, className = '' }) {
  return (
    <div className={`text-center py-14 px-6 ${className}`}>
      {Icon && (
        <div className="w-11 h-11 rounded-full bg-white/[0.04] border border-[var(--border-subtle)] flex items-center justify-center mx-auto mb-4">
          <Icon size={20} weight="regular" className="text-[var(--text-dim)]" />
        </div>
      )}
      {title && <p className="text-sm font-semibold text-[var(--text-primary)] mb-1.5">{title}</p>}
      {sub && <p className="text-xs text-[var(--text-dim)] max-w-xs mx-auto leading-relaxed">{sub}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
