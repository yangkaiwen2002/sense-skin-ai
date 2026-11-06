import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CaretRight, Calculator, CheckCircle } from '@phosphor-icons/react'
import { getItemOverview, rentVsBuy } from '../services/api'
import SearchBar from '../components/SearchBar'
import SkinImage from '../components/SkinImage'
import QuoteSource from '../components/QuoteSource'
import RentVsBuyCard from '../components/RentVsBuyCard'
import Button from '../components/ui/Button'
import { formatCNY } from '../utils/formatters'

export default function RentVsBuy() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const initialItem = params.get('item')
  const [selected, setSelected] = useState(null), [days, setDays] = useState(7), [budget, setBudget] = useState(1000)
  const [result, setResult] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState('')
  const [selecting, setSelecting] = useState(false)
  const version = useRef(0)
  useEffect(() => {
    let ignore = false
    version.current++
    setResult(null); setSelected(null); setError(''); setLoading(false); setSelecting(false)
    if (!initialItem) return
    setSelecting(true)
    getItemOverview(initialItem).then(item => {
      if (ignore) return
      if (item) setSelected({ ...item, id: item.item_id, quote: item.platforms?.[0] })
      else setError('预选饰品无法载入，请重新搜索。')
      setSelecting(false)
    })
    return () => { ignore = true }
  }, [initialItem])
  useEffect(() => () => { version.current++ }, [])
  function select(item) { version.current++; setSelected(item); setResult(null); setError('') }
  function edit(setter, value) { setter(value); setResult(null); setError('') }
  async function submit(e) {
    e.preventDefault()
    if (!selected) return
    const requestVersion = ++version.current
    setLoading(true); setError(''); setResult(null)
    const data = await rentVsBuy(selected.id, { days: Number(days), budget: Number(budget) })
    if (requestVersion !== version.current) return
    setLoading(false)
    if (data) setResult(data)
    else setError('计算暂时失败，请检查输入或稍后重试。')
  }
  return <div className="page-shell">
    <div className="breadcrumb"><button onClick={() => navigate('/')}>饰品市场</button><CaretRight size={12} /><span>租买计算</span></div>
    <div className="page-heading"><div><span className="eyebrow">RENT OR BUY</span><h1>短期用，还是长期留？</h1><p>比较使用成本，也看清购买本金与押金需求。</p></div></div>
    <div className="rental-layout">
      <div>
        <form onSubmit={submit} className="surface-card p-5 sm:p-7">
          <fieldset disabled={loading || selecting} className="space-y-6 min-w-0">
            <div><p className="field-label">01 · 选择饰品</p>
              {selecting ? <p role="status" className="muted-copy">正在载入饰品…</p> : selected ? <div className="selected-item">
                <SkinImage iconUrl={selected.icon_url} name={selected.item_name} />
                <div><strong>{selected.item_name}</strong><QuoteSource quote={selected.quote || selected} compact /></div>
                <Button size="sm" variant="ghost" onClick={() => select(null)}>更换</Button>
              </div> : <SearchBar label="选择计算饰品" placeholder="搜索想使用的饰品…" onSelect={select} />}
            </div>
            <div className="form-row">
              <div><label className="field-label" htmlFor="rental-days">02 · 使用天数</label>
                <div className="flex gap-1 mb-3">{[3, 7, 14, 30].map(d => <button type="button" key={d} className={`filter-tab ${Number(days) === d ? 'is-active' : ''}`} aria-pressed={Number(days) === d} onClick={() => edit(setDays, d)}>{d}天</button>)}</div>
                <input id="rental-days" className="field-input" type="number" min="1" max="365" required value={days} onChange={e => edit(setDays, e.target.value)} />
                <p className="field-help">支持 1–365 天。</p>
              </div>
              <div><label className="field-label" htmlFor="rental-budget">03 · 可用预算（元）</label>
                <p className="field-help mb-3 min-h-[40px]">用于判断是否能承担前期资金。</p>
                <input id="rental-budget" className="field-input" type="number" min="0" step="0.01" required value={budget} onChange={e => edit(setBudget, e.target.value)} />
                <p className="field-help">押金金额未知时，不会视为零押金。</p>
              </div>
            </div>
            <Button type="submit" variant="primary" disabled={!selected} loading={loading} className="w-full"><Calculator size={18} />{loading ? '正在比较方案…' : '比较租赁与购买'}</Button>
          </fieldset>
        </form>
        {error && <p role="alert" className="notice notice-error">{error}</p>}
        {result && <section className="mt-6" aria-label="租买分析结果" aria-live="polite">
          <div className="flex items-center gap-2 mb-3"><CheckCircle size={19} className="text-[var(--accent)]" /><h2 className="text-base font-semibold">{result.days} 天使用方案</h2></div>
          <p className="muted-copy mb-3">{result.item_name} · 预算 {formatCNY(result.budget)}</p>
          <RentVsBuyCard {...result} />
          <div className="flex gap-3 flex-wrap mt-4"><Button onClick={() => navigate(`/item/${result.item_id}`)}>查看饰品研究</Button><Button variant="ghost" onClick={() => navigate(`/compare/${result.item_id}`)}>核对平台报价</Button></div>
        </section>}
      </div>
      <aside className="calculation-notes"><h2>计算前，了解这些假设</h2><ol>
        <li><strong>租赁成本</strong><br />按已有日租与周租报价计算。租赁数据目前仍为演示数据。</li>
        <li><strong>购买成本</strong><br />展示转卖损耗情景，默认按购买价的 4% 计算；购买时仍需支付全部本金。</li>
        <li><strong>尚未包含</strong><br />平台手续费、未来涨跌以及未知的押金金额。结果用于比较，不是收益预测。</li>
      </ol></aside>
    </div>
  </div>
}
