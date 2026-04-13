import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchItems } from '../services/api'

export default function SearchBar({ placeholder = '搜索饰品，例如：AK-47 红线、爪子刀' }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const timer = useRef(null)
  const navigate = useNavigate()

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setResults([]); return }
    setLoading(true)
    const data = await searchItems(q)
    setResults(data || [])
    setLoading(false)
    setOpen(true)
  }, [])

  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => doSearch(query), 300)
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
    if (e.key === 'Enter' && results.length > 0) select(results[0])
  }

  return (
    <div ref={ref} className="relative w-full">
      <div className="relative">
        <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          className="w-full bg-slate-800 border border-slate-600 rounded-xl pl-12 pr-4 py-3.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition"
        />
        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
          </div>
        )}
      </div>
      {open && results.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
          {results.map(item => (
            <button
              key={item.id}
              onMouseDown={() => select(item)}
              className="w-full text-left px-4 py-3 text-sm text-slate-200 hover:bg-slate-700 hover:text-white transition-colors border-b border-slate-700/50 last:border-0"
            >
              {item.item_name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
