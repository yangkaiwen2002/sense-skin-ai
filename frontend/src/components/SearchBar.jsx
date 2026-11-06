import { useState, useEffect, useRef, useId } from 'react'
import { useNavigate } from 'react-router-dom'
import { MagnifyingGlass, X } from '@phosphor-icons/react'
import { searchItems } from '../services/api'
import { formatCNY } from '../utils/formatters'
import QuoteSource from './QuoteSource'

export default function SearchBar({ placeholder = '搜索饰品名称、武器或皮肤…', label = '搜索饰品', onSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [retry, setRetry] = useState(0)
  const root = useRef(null), input = useRef(null)
  const listId = useId()
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return
    let ignore = false
    setLoading(true)
    setFailed(false)
    setResults([])
    setActive(-1)
    const timer = setTimeout(async () => {
      const data = await searchItems(query.trim())
      if (ignore) return
      setFailed(data === null)
      setResults(Array.isArray(data) ? data : data?.items || [])
      setLoading(false)
    }, query ? 200 : 0)
    return () => { ignore = true; clearTimeout(timer) }
  }, [query, open, retry])

  useEffect(() => {
    const outside = e => { if (!root.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [])

  useEffect(() => {
    root.current?.querySelector(`[data-search-index="${active}"]`)?.scrollIntoView({ block: 'nearest' })
  }, [active])

  function select(item) {
    setOpen(false)
    setQuery('')
    if (onSelect) onSelect(item)
    else navigate(`/item/${item.id}`)
  }
  function keyDown(e) {
    if (e.nativeEvent.isComposing) return
    if (e.key === 'Escape') { setOpen(false); return }
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive(i => Math.min(i + 1, results.length - 1)) }
    if (e.key === 'ArrowUp') { e.preventDefault(); setActive(i => Math.max(i - 1, 0)) }
    if (e.key === 'Enter' && open && results.length && !loading) { e.preventDefault(); select(results[Math.max(active, 0)]) }
  }
  return (
    <div ref={root} className="search-control" onBlur={e => { if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false) }}>
      <div className="search-input-wrap">
        <MagnifyingGlass size={19} aria-hidden="true" />
        <input ref={input} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={listId}
          aria-activedescendant={open && active >= 0 ? `${listId}-${active}` : undefined}
          autoComplete="off" aria-label={label} placeholder={placeholder} value={query}
          onFocus={() => setOpen(true)} onChange={e => { setQuery(e.target.value); setResults([]); setOpen(true) }} onKeyDown={keyDown} />
        {query && <button type="button" aria-label="清除搜索" onClick={() => { setQuery(''); input.current?.focus() }}><X size={16} /></button>}
      </div>
      {open && <div className="search-menu">
        <p className="search-caption">{query ? '匹配的饰品' : '浏览饰品'}</p>
        {loading && <p className="search-message" role="status">正在搜索…</p>}
        {failed && <div className="search-message" role="alert">暂时无法搜索。<button type="button" className="text-action" onClick={() => setRetry(x => x + 1)}>重试</button></div>}
        {!loading && !failed && !results.length && <p className="search-message" role="status">没有找到相关饰品，试试武器名称或其他关键词。</p>}
        <div id={listId} role="listbox" aria-label="搜索结果">
          {results.map((item, i) => <button type="button" role="option" id={`${listId}-${i}`} data-search-index={i} key={item.id}
            aria-selected={i === active} className="search-result" tabIndex={-1}
            onMouseDown={e => e.preventDefault()} onClick={() => select(item)} onMouseEnter={() => setActive(i)}>
            <span className="search-result-copy"><strong>{item.item_name || item.skin_name}</strong><small>{[item.weapon_type, item.exterior].filter(Boolean).join(' · ')}</small><QuoteSource quote={item} compact /></span>
            <span className="search-result-price"><strong>{formatCNY(item.current_price)}</strong><small>{item.platform || '暂无平台报价'}</small></span>
          </button>)}
        </div>
      </div>}
    </div>
  )
}
