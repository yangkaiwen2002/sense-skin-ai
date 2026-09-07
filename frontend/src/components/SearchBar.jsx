import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { MagnifyingGlass } from '@phosphor-icons/react'
import { searchItems } from '../services/api'
import { formatCNY } from '../utils/formatters'
import { RARITY_COLOR } from '../utils/constants'

function highlight(text, query) {
  if (!query || !text) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text
  return (
    <>
      {text.slice(0, idx)}
      <mark className="bg-[var(--accent-soft)] text-[var(--accent-strong)] rounded-sm px-px">
        {text.slice(idx, idx + query.length)}
      </mark>
      {text.slice(idx + query.length)}
    </>
  )
}

export default function SearchBar({ placeholder = '搜索饰品，例如：AK-47 红线、爪子刀…' }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const ref = useRef(null)
  const inputRef = useRef(null)
  const timer = useRef(null)
  const navigate = useNavigate()

  const doSearch = useCallback(async (q) => {
    setLoading(true)
    const data = await searchItems(q)
    setResults(data || [])
    setLoading(false)
    setOpen(true)
    setActiveIdx(-1)
  }, [])

  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => doSearch(query), query ? 200 : 0)
    return () => clearTimeout(timer.current)
  }, [query, doSearch])

  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  function select(item) {
    setQuery('')
    setOpen(false)
    navigate(`/item/${item.id}`)
  }

  function onKeyDown(e) {
    if (!open || results.length === 0) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, -1)) }
    else if (e.key === 'Enter') { if (activeIdx >= 0) select(results[activeIdx]); else if (results.length > 0) select(results[0]) }
    else if (e.key === 'Escape') setOpen(false)
  }

  return (
    <div ref={ref} className="relative w-full">
      <div className="relative">
        <MagnifyingGlass
          size={18}
          weight="bold"
          className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-opacity duration-150"
          style={{ opacity: loading ? 0 : 0.4, color: 'var(--text-secondary)' }}
        />
        {loading && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
            <div className="w-4 h-4 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--accent-border)', borderTopColor: 'var(--accent)' }} />
          </div>
        )}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => doSearch(query)}
          placeholder={placeholder}
          className={`w-full min-h-[44px] bg-white/[0.05] border text-[var(--text-primary)] text-sm outline-none
            pl-12 pr-4 py-3 transition-colors duration-150
            ${open && results.length > 0 ? 'rounded-t-[var(--radius-md)]' : 'rounded-[var(--radius-md)]'}`}
          style={{ borderColor: open ? 'var(--accent-border)' : 'var(--border-default)' }}
        />
      </div>

      {open && results.length > 0 && (
        <div
          className="absolute top-full left-0 right-0 rounded-b-[var(--radius-md)] border border-t-0 overflow-hidden z-[200]"
          style={{ background: 'var(--bg-surface-raised)', borderColor: 'var(--accent-border)', boxShadow: 'var(--shadow-lg)' }}
        >
          <div className="px-3.5 py-1.5 text-[10px] uppercase tracking-wide text-[var(--text-dim)] border-b border-white/[0.04]" style={{ background: 'rgba(0,0,0,0.2)' }}>
            {query ? `"${query}" 的搜索结果` : '热门饰品'}
          </div>

          {results.map((item, i) => {
            const rc = RARITY_COLOR[item.rarity] || 'var(--accent)'
            const isActive = i === activeIdx
            return (
              <button
                key={item.id}
                onMouseDown={() => select(item)}
                onMouseEnter={() => setActiveIdx(i)}
                className="w-full text-left min-h-[52px] px-3.5 py-2 flex items-center gap-2.5 text-[13px] text-[var(--text-primary)] transition-colors duration-100 border-0"
                style={{
                  background: isActive ? 'var(--accent-soft)' : 'transparent',
                  borderBottom: i < results.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                }}
              >
                <div className="w-2 h-2 rounded-full shrink-0" style={{ background: rc, boxShadow: `0 0 6px ${rc}80` }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold whitespace-nowrap overflow-hidden text-ellipsis">
                      {highlight(item.skin_name || item.item_name, query)}
                    </span>
                    {item.stattrak && (
                      <span className="text-[9px] font-bold shrink-0 rounded px-1 py-px" style={{ color: 'var(--gold)', background: 'var(--gold-soft)', border: '1px solid var(--gold-border)' }}>ST</span>
                    )}
                  </div>
                  <div className="text-[11px] text-[var(--text-dim)] mt-0.5">{[item.weapon_type, item.exterior].filter(Boolean).join(' · ')}</div>
                </div>
                {item.current_price != null && (
                  <div className="text-right shrink-0">
                    <div className="price-display text-sm">{formatCNY(item.current_price)}</div>
                    {item.platform && <div className="text-[10px] text-[var(--text-dim)] mt-0.5">{item.platform}</div>}
                  </div>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
