export default function Card({ as: Tag = 'div', className = '', padded = true, children, ...props }) {
  return (
    <Tag
      className={`bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-[var(--radius-md)]
        ${padded ? 'p-4 sm:p-5' : ''} ${className}`}
      {...props}
    >
      {children}
    </Tag>
  )
}

export function CardHeader({ title, sub, action, className = '' }) {
  return (
    <div className={`flex items-center justify-between gap-3 mb-3.5 ${className}`}>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-[var(--text-primary)] truncate">{title}</p>
        {sub && <p className="text-xs text-[var(--text-dim)] mt-0.5">{sub}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
