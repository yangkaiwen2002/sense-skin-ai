import { forwardRef } from 'react'

const VARIANTS = {
  primary: 'bg-[var(--accent)] text-white border border-transparent hover:bg-[var(--accent-strong)]',
  secondary: 'bg-[var(--bg-surface-raised)] text-[var(--text-primary)] border border-[var(--border-default)] hover:bg-[var(--bg-surface-sunken)] hover:border-[var(--border-strong)]',
  ghost: 'bg-transparent text-[var(--text-secondary)] border border-transparent hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-sunken)]',
  gold: 'bg-[var(--gold-soft)] text-[var(--gold-strong)] border border-[var(--gold-border)] hover:bg-[var(--gold-soft)] hover:border-[var(--gold)]',
}

const SIZES = {
  sm: 'text-xs px-3 py-1.5 gap-1.5 rounded-[var(--radius-sm)]',
  md: 'text-sm px-4 py-2.5 gap-2 rounded-[var(--radius-sm)]',
}

const Button = forwardRef(function Button(
  { variant = 'secondary', size = 'md', className = '', disabled, loading, children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      type="button"
      aria-busy={loading || undefined}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center font-semibold whitespace-nowrap
        transition-[transform,background-color,border-color,opacity] duration-150 ease-standard
        active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100
        min-h-[40px] ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {loading ? (
        <span
          className="w-3.5 h-3.5 rounded-full border-2 border-current border-t-transparent animate-spin opacity-70"
          aria-hidden
        />
      ) : null}
      {children}
    </button>
  )
})

export default Button
