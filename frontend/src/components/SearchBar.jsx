import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchItems } from '../services/api'
import { formatCNY } from '../utils/formatters'

const RARITY_COLOR = {
  '违禁': '#e4ae39', '隐秘': '#eb4b4b', '保密': '#d32ce6',
  '受限': '#8847ff', '军规': '#4b69ff', '精工': '#5e98d9',
}

function highlight(text, query) {
  if (!query || !text) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text
  return (
    <>
      {text.slice(0, idx)}
      <mark style={{ background: 'rgba(74,142,245,0.3)', color: '#7eb3ff', borderRadius: 2, padding: '0 1px' }}>
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
    // Show suggestions immediately on focus (empty query = top items)
    timer.current = setTimeout(() => doSearch(query), query ? 200 : 0)
    return () => clearTimeout(timer.current)
  }, [query, doSearch])

  // Close on outside click
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
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx(i => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx(i => Math.max(i - 1, -1))
    } else if (e.key === 'Enter') {
      if (activeIdx >= 0) select(results[activeIdx])
      else if (results.length > 0) select(results[0])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div ref={ref} style={{ position: 'relative', width: '100%' }}>
      <div style={{ position: 'relative' }}>
        {/* Search icon */}
        <svg
          style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', opacity: loading ? 0 : 0.35, pointerEvents: 'none', transition: 'opacity 0.15s' }}
          width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>

        {/* Loading spinner */}
        {loading && (
          <div style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
            <div style={{
              width: 16, height: 16, borderRadius: '50%',
              border: '2px solid rgba(74,142,245,0.2)',
              borderTopColor: '#4a8ef5',
              animation: 'spin 0.7s linear infinite',
            }} />
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
          style={{
            width: '100%',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: open && results.length > 0 ? '10px 10px 0 0' : 10,
            paddingLeft: 48,
            paddingRight: 16,
            paddingTop: 14,
            paddingBottom: 14,
            color: 'var(--text-primary)',
            fontSize: 14,
            outline: 'none',
            transition: 'border-color 0.15s ease, border-radius 0.1s ease',
            borderColor: open ? 'rgba(74,142,245,0.4)' : 'rgba(255,255,255,0.1)',
          }}
        />
      </div>

      {/* Dropdown */}
      {open && results.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: '#111827',
          border: '1px solid rgba(74,142,245,0.25)',
          borderTop: 'none',
          borderRadius: '0 0 12px 12px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
          overflow: 'hidden',
          zIndex: 200,
        }}>
          {/* Header */}
          <div style={{
            padding: '7px 14px',
            fontSize: 10, color: 'var(--text-dim)',
            letterSpacing: '0.08em', textTransform: 'uppercase',
            borderBottom: '1px solid rgba(255,255,255,0.04)',
            background: 'rgba(0,0,0,0.2)',
          }}>
            {query ? `"${query}" 的搜索结果` : '热门饰品'}
          </div>

          {results.map((item, i) => {
            const rc = RARITY_COLOR[item.rarity] || '#4a8ef5'
            const isActive = i === activeIdx
            return (
              <button
                key={item.id}
                onMouseDown={() => select(item)}
                onMouseEnter={() => setActiveIdx(i)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '9px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  fontSize: 13,
                  color: 'var(--text-primary)',
                  background: isActive ? 'rgba(74,142,245,0.08)' : 'transparent',
                  border: 'none',
                  borderBottom: i < results.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  cursor: 'pointer',
                  transition: 'background 0.1s',
                }}
              >
                {/* Rarity dot */}
                <div style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: rc, flexShrink: 0,
                  boxShadow: `0 0 6px ${rc}80`,
                }} />

                {/* Name block */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {highlight(item.skin_name || item.item_name, query)}
                    </span>
                    {item.stattrak && (
                      <span style={{
                        fontSize: 9, fontWeight: 700, color: '#f5a623',
                        background: 'rgba(245,166,35,0.12)', border: '1px solid rgba(245,166,35,0.25)',
                        borderRadius: 3, padding: '1px 4px', flexShrink: 0,
                      }}>ST</span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 1 }}>
                    {[item.weapon_type, item.exterior].filter(Boolean).join(' · ')}
                  </div>
                </div>

                {/* Price */}
                {item.current_price != null && (
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div className="price-display" style={{ fontSize: 14 }}>
                      {formatCNY(item.current_price)}
                    </div>
                    {item.platform && (
                      <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 1 }}>
                        {item.platform}
                      </div>
                    )}
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
