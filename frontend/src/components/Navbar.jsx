import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()

  const links = [
    { to: '/', label: '首页' },
    { to: '/rent-vs-buy', label: '租买对比' },
    { to: '/watchlist', label: '收藏夹' },
  ]

  return (
    <nav className="bg-slate-900 border-b border-slate-700/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-cyan-400" />
          </div>
          <span className="font-bold text-white text-lg tracking-tight">SkinSense</span>
          <span className="font-bold text-cyan-400 text-lg tracking-tight">AI</span>
        </Link>
        <div className="flex items-center gap-1">
          {links.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pathname === to
                  ? 'bg-cyan-500/20 text-cyan-300'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
