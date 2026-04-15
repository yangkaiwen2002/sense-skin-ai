import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()

  const links = [
    { to: '/', label: '市场' },
    { to: '/rent-vs-buy', label: '租买计算' },
    { to: '/watchlist', label: '自选' },
  ]

  return (
    <nav
      style={{
        background: 'rgba(14,17,23,0.92)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div
            style={{
              width: 28,
              height: 28,
              background: 'linear-gradient(135deg, #4a8ef5 0%, #2563eb 100%)',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 12px rgba(74,142,245,0.35)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="flex items-baseline gap-0.5">
            <span className="font-bold text-white text-base tracking-tight">Skin</span>
            <span style={{ color: '#4a8ef5', fontWeight: 700, fontSize: '1rem' }}>Sense</span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: 'rgba(255,255,255,0.35)',
                letterSpacing: '0.08em',
                marginLeft: 4,
                textTransform: 'uppercase',
              }}
            >
              AI
            </span>
          </div>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {links.map(({ to, label }) => {
            const active = pathname === to
            return (
              <Link
                key={to}
                to={to}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? '#e8eaf0' : 'var(--text-secondary)',
                  background: active ? 'rgba(255,255,255,0.07)' : 'transparent',
                  transition: 'all 0.15s ease',
                  textDecoration: 'none',
                  border: active ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent',
                }}
              >
                {label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
