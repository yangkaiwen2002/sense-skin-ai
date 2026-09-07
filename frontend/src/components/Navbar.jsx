import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { List, X } from '@phosphor-icons/react'

const LINKS = [
  { to: '/', label: '市场' },
  { to: '/rent-vs-buy', label: '租买计算' },
  { to: '/watchlist', label: '自选' },
]

function Wordmark() {
  return (
    <Link to="/" className="flex items-center gap-2.5 shrink-0">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
          stroke="var(--accent)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="font-bold text-[var(--text-primary)] text-[15px] tracking-tight">
        SenseSkin
        <span className="ml-1.5 text-[10px] font-semibold text-[var(--accent-strong)] tracking-widest align-middle">AI</span>
      </span>
    </Link>
  )
}

function NavLink({ to, label, active, onClick, mobile = false }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={`px-3.5 rounded-[var(--radius-sm)] text-sm transition-colors duration-150 flex items-center
        ${mobile ? 'min-h-[44px]' : 'py-2'}
        ${active
          ? 'font-semibold text-[var(--text-primary)] bg-white/[0.07] border border-[var(--border-default)]'
          : 'font-normal text-[var(--text-secondary)] border border-transparent hover:text-[var(--text-primary)] hover:bg-white/[0.04]'
        }`}
    >
      {label}
    </Link>
  )
}

export default function Navbar() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-50 bg-[#08090b]/92 backdrop-blur-md border-b border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Wordmark />

        {/* Desktop links */}
        <div className="hidden sm:flex items-center gap-1">
          {LINKS.map(l => (
            <NavLink key={l.to} {...l} active={pathname === l.to} />
          ))}
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          aria-label={open ? '关闭菜单' : '打开菜单'}
          aria-expanded={open}
          className="sm:hidden w-10 h-10 -mr-2 flex items-center justify-center rounded-[var(--radius-sm)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.05] active:scale-95 transition"
        >
          {open ? <X size={20} /> : <List size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="sm:hidden border-t border-[var(--border-subtle)] px-4 py-3 flex flex-col gap-1 animate-up">
          {LINKS.map(l => (
            <NavLink key={l.to} {...l} mobile active={pathname === l.to} onClick={() => setOpen(false)} />
          ))}
        </div>
      )}
    </nav>
  )
}
