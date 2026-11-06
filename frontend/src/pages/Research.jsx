import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Sparkle, Plus, ArrowUp, Stop, CheckCircle, WarningCircle, Circle, CaretDown, DownloadSimple, X, BookOpen, ArrowUpRight } from '@phosphor-icons/react'
import { BASE_URL, getItemOverview } from '../services/api'
import { consumeSSE } from '../utils/sse'
import SearchBar from '../components/SearchBar'
import QuoteSource from '../components/QuoteSource'
import Button from '../components/ui/Button'
import ErrorState from '../components/ui/ErrorState'
import { formatCNY } from '../utils/formatters'

const MODES = [{ id: 'market', label: '行情研究' }, { id: 'compare', label: '平台比较' }, { id: 'rental', label: '租买决策' }, { id: 'knowledge', label: '知识问答' }]
const EXAMPLES = [
  { mode: 'market', short: '查行情', title: '这件饰品现在什么情况？', sub: '核对最新报价、数据来源与相关公告' },
  { mode: 'compare', short: '比平台', title: '不同平台的价差可信吗？', sub: '区分真实报价、过期快照和未知费用' },
  { mode: 'rental', short: '算租买', title: '短期用，租还是买？', sub: '一起看租金、购买本金和押金缺口' },
]
async function api(path, options) {
  const response = await fetch(`${BASE_URL}/research${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : '研究服务暂时不可用，请重试。')
  }
  return response.json()
}
function Source({ source, runId }) {
  const url = source.url && (source.url.startsWith('/') && !source.url.startsWith('//') || /^https:\/\//.test(source.url)) ? source.url : null
  return <details className="research-source" id={`source-${runId}-${source.id}`}>
    <summary><span className="source-index">{source.id}</span><span><small>{{ market: '行情快照', news: '官方公告 · 影响待评估', knowledge: '静态知识资料', rental: '租买计算 · 演示租金' }[source.kind]}{source.data?.published_at && ` · ${new Date(source.data.published_at).toLocaleDateString('zh-CN')}`}</small><strong>{source.title}</strong></span><CaretDown size={14} /></summary>
    <div className="research-source-body">
      {source.kind === 'market' ? source.data?.overview?.platforms?.map(p => <div className="research-quote" key={p.platform}><div><strong>{p.platform}</strong><span className="price-display">{formatCNY(p.current_price)}</span></div><QuoteSource quote={p} /></div>) : <p>{source.summary}</p>}
      {source.data?.fetched_at && <p className="muted-copy">采集于 {new Date(source.data.fetched_at).toLocaleString('zh-CN', { hour12: false })}</p>}
      {url && <a href={url} target={url.startsWith('https:') ? '_blank' : undefined} rel="noreferrer">{source.kind === 'news' ? '查看官方原文' : '查看完整数据'} <ArrowUpRight size={14} /></a>}
    </div>
  </details>
}
function Answer({ run }) {
  const ids = new Set(run.sources?.map(s => s.id))
  return <div className="research-answer">{run.answer.split(/(\[S\d+\])/g).map((part, i) => {
    const id = part.slice(1, -1)
    return ids.has(id) ? <a href={`#source-${run.id}-${id}`} key={i} onClick={() => {
      const el = document.getElementById(`source-${run.id}-${id}`)
      if (el) el.open = true
    }}>{part}</a> : part
  })}</div>
}
function Run({ run, onRetry, busy }) {
  return <article className="research-turn">
    <div className="research-user"><span>你的研究目标</span><h2>{run.question}</h2></div>
    <div className="research-response"><div className="research-response-heading"><Sparkle size={18} weight="fill" /><strong>SenseSkin</strong><span className={`source-badge ${run.answer_mode === 'generated' ? 'source-observed' : 'source-unknown'}`}>{run.answer_mode === 'generated' ? 'AI 研究' : '证据工作流'}</span></div>
      <details className="research-trace" open={run.status === 'running'}><summary>{run.status === 'running' ? '正在执行研究' : '查看执行过程'} · {run.steps?.length || 0} 个步骤<CaretDown size={13} /></summary>
        <ol>{run.steps?.map(step => <li key={step.id} className={`step-${step.status}`}>
          {step.status === 'done' ? <CheckCircle size={16} /> : ['warning', 'error', 'failed', 'cancelled', 'interrupted'].includes(step.status) ? <WarningCircle size={16} /> : <Circle size={16} className="animate-pulse" />}
          <div><strong>{step.label}</strong>{step.summary && <p>{step.summary}</p>}</div>{step.duration_ms != null && <small>{(step.duration_ms / 1000).toFixed(1)}s</small>}
        </li>)}</ol>
      </details>
      {run.answer && <Answer run={run} />}
      {run.error && <p className="notice notice-error" role="alert">{run.error}</p>}
      {run.status === 'running' && !run.answer && <p role="status" className="muted-copy py-3">正在收集可核对的证据…</p>}
      {run.sources?.length > 0 && <div className="research-sources"><h3><BookOpen size={15} />本轮证据 <span>{run.sources.length}</span></h3>{run.sources.map(source => <Source key={source.id} source={source} runId={run.id} />)}</div>}
      {run.artifact && <a className="research-artifact" href={`${BASE_URL}/research/runs/${run.id}/artifact`}><DownloadSimple size={21} /><span><strong>{run.answer_mode === 'generated' ? '研究报告' : '证据记录'}</strong><small>包含本轮结论、来源与生成时间 · Markdown</small></span><ArrowUpRight size={17} /></a>}
      {['failed', 'cancelled', 'interrupted'].includes(run.status) && <Button size="sm" className="mt-3" disabled={busy} onClick={() => onRetry(run)}>重新研究这个问题</Button>}
    </div>
  </article>
}

export default function Research() {
  const { sessionId } = useParams(), [params] = useSearchParams(), navigate = useNavigate()
  const initialItem = params.get('item')
  const [sessions, setSessions] = useState([]), [session, setSession] = useState(null), [runs, setRuns] = useState([])
  const [service, setService] = useState(null), [selected, setSelected] = useState([]), [question, setQuestion] = useState('')
  const [mode, setMode] = useState('market'), [refresh, setRefresh] = useState(true), [days, setDays] = useState(7), [budget, setBudget] = useState(1000)
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(false), [error, setError] = useState(''), [historyOpen, setHistoryOpen] = useState(false)
  const [notice, setNotice] = useState(''), [reload, setReload] = useState(0)
  const abort = useRef(null), version = useRef(0), activeId = useRef(null), input = useRef(null)
  const running = busy || Boolean(session?.active_run_id)

  function restoreParameters(run) {
    const p = run?.parameters || {}
    setMode(p.mode || 'market'); setRefresh(p.refresh ?? true); setDays(p.days ?? 7); setBudget(p.budget ?? 1000)
  }

  async function list() { const data = await api('/sessions'); setSessions(data.sessions) }
  useEffect(() => {
    let ignore = false
    Promise.all([api('/sessions'), api('/status')]).then(([history, status]) => { if (!ignore) { setSessions(history.sessions); setService(status) } }).catch(e => { if (!ignore) setError(e.message) })
    return () => { ignore = true }
  }, [reload])
  useEffect(() => {
    // New sessions replace the URL while their first run is streaming.
    if (sessionId && activeId.current === sessionId) return
    const requestVersion = ++version.current
    abort.current?.abort(); setBusy(false); setError(''); setNotice(''); setHistoryOpen(false)
    setSession(null); setRuns([]); setSelected([]); setQuestion(''); activeId.current = sessionId || null
    if (!sessionId) {
      restoreParameters()
      setLoading(Boolean(initialItem))
      if (initialItem) getItemOverview(initialItem).then(item => {
        if (requestVersion !== version.current) return
        if (item) setSelected([{ ...item, id: item.item_id }]); else setError('预选饰品无法载入，请重新选择。')
        setLoading(false)
      })
      return
    }
    setLoading(true)
    api(`/sessions/${sessionId}`).then(async data => {
      const items = await Promise.all(data.item_ids.map(getItemOverview))
      if (requestVersion !== version.current) return
      setSession(data); setRuns(data.runs); restoreParameters(data.runs.at(-1)); setSelected(items.filter(Boolean).map(item => ({ ...item, id: item.item_id }))); setLoading(false)
    }).catch(e => { if (requestVersion === version.current) { setError(e.message); setLoading(false) } })
  }, [sessionId, initialItem, reload])
  useEffect(() => () => { version.current++; abort.current?.abort() }, [])
  useEffect(() => {
    if (busy || !session?.active_run_id) return
    let ignore = false
    const timer = setInterval(() => api(`/sessions/${session.id}`).then(data => { if (!ignore) { setSession(data); setRuns(data.runs); if (data.runs.at(-1)?.status === 'cancelled') setNotice('') } }).catch(() => {}), 2000)
    return () => { ignore = true; clearInterval(timer) }
  }, [session?.id, session?.active_run_id, busy])

  function choose(item) {
    if (selected.some(s => s.id === item.id)) return
    if (selected.length >= 3) { setError('每次最多研究 3 件饰品。'); return }
    setSelected(items => [...items, item]); setError('')
  }
  async function retryRun(run) {
    const currentVersion = version.current
    setLoading(true)
    const items = await Promise.all(run.item_ids.map(getItemOverview))
    if (currentVersion !== version.current) return
    setLoading(false)
    if (items.some(item => !item)) { setError('原研究饰品暂时无法载入，请稍后重试。'); return }
    setSelected(items.map(item => ({ ...item, id: item.item_id })))
    restoreParameters(run); setQuestion(run.question); input.current?.focus()
  }
  async function submit(e) {
    e.preventDefault()
    if (!question.trim() || running || loading) return
    if (mode !== 'knowledge' && !selected.length) { setError('先选择饰品，或切换到知识问答。'); return }
    const requestVersion = ++version.current, ctrl = new AbortController()
    abort.current = ctrl; setBusy(true); setError(''); setNotice('')
    let current = session, runId
    const text = question.trim()
    try {
      if (!current) {
        current = await api('/sessions', { method: 'POST', body: JSON.stringify({ title: text.slice(0, 80) }), signal: ctrl.signal })
        if (requestVersion !== version.current) return
        activeId.current = current.id; setSession(current); navigate(`/research/${current.id}`, { replace: true })
      }
      const response = await fetch(`${BASE_URL}/research/sessions/${current.id}/runs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctrl.signal,
        body: JSON.stringify({ request_id: crypto.randomUUID(), question: text, item_ids: selected.map(i => i.id), mode, refresh, days: Number(days), budget: Number(budget) }),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(typeof data.detail === 'string' ? data.detail : '研究启动失败，请重试。')
      }
      setQuestion('')
      await consumeSSE(response.body, event => {
        if (requestVersion !== version.current) return
        if (event.type === 'run') {
          runId = event.run.id
          setRuns(old => [...old.filter(r => r.id !== runId), event.run])
          setSession(old => ({ ...old, active_run_id: runId }))
        } else if (event.type === 'completed') {
          runId = event.run.id
          setRuns(old => old.some(r => r.id === runId) ? old.map(r => r.id === runId ? event.run : r) : [...old, event.run])
          setSession(old => ({ ...old, active_run_id: null }))
        } else if (event.type === 'notice') setNotice(event.text)
        else setRuns(old => old.map(run => {
          if (run.id !== runId) return run
          if (event.type === 'step') return { ...run, steps: [...run.steps.filter(s => s.id !== event.step.id), event.step], answer_mode: event.step.id === 'synthesis' ? 'generated' : run.answer_mode }
          if (event.type === 'sources') return { ...run, sources: event.sources }
          if (event.type === 'text') return { ...run, answer: run.answer + event.text }
          if (event.type === 'error') return { ...run, error: event.error }
          return run
        }))
      })
    } catch (e) {
      if (requestVersion === version.current) {
        if (e.name === 'AbortError') setNotice('已请求停止，正在保留本轮证据。')
        else setError(e.message || '连接中断，已保留收到的研究内容。')
      }
    } finally {
      if (requestVersion === version.current) {
        setBusy(false)
        list().catch(() => {})
        if (current) api(`/sessions/${current.id}`).then(data => { if (requestVersion === version.current) { setSession(data); setRuns(data.runs); if (data.runs.at(-1)?.status === 'cancelled') setNotice('') } }).catch(() => {})
      }
    }
  }

  return <div className="agent-workspace">
    <aside className="research-rail">
      <div className="research-rail-heading"><span><Sparkle size={17} />研究工作台</span><button className="research-history-toggle" aria-expanded={historyOpen} onClick={() => setHistoryOpen(x => !x)}>历史<CaretDown size={14} /></button></div>
      <Button variant="primary" className="w-full" disabled={running} onClick={() => { activeId.current = null; navigate('/research'); if (!sessionId) { setQuestion(''); setSelected([]); setRuns([]) } }}><Plus size={16} />开始新研究</Button>
      <div className={`research-history ${historyOpen ? 'is-open' : ''}`}><h2>最近的研究</h2>{sessions.length ? sessions.map(s => <button key={s.id} disabled={running} className={s.id === sessionId ? 'is-active' : ''} onClick={() => { activeId.current = null; navigate(`/research/${s.id}`) }}><strong>{s.title}</strong><small>{new Date(s.updated_at).toLocaleDateString('zh-CN')}</small></button>) : <p>完成一次研究后，可在这里继续。</p>}</div>
      <Link className="research-market-link" to="/">浏览饰品市场 <ArrowUpRight size={14} /></Link>
    </aside>
    <div className="agent-main">
      <header className="research-topline"><span>{session?.title || '新的饰品研究'}</span><span className={`source-badge ${service?.model?.configured ? 'source-observed' : 'source-demo'}`}>{service?.model?.configured ? '模型已配置' : service ? '证据模式' : '检查连接中'}</span></header>
      {!runs.length && !loading && <div className="research-welcome"><span className="eyebrow">ASK SENSESKIN</span><h1>你的问题，让证据来回答。</h1><p>选择饰品，说出目标。我们一起核对行情、比较方案、追踪来源。</p><div className="research-examples">{EXAMPLES.map(example => <button key={example.mode} disabled={running} onClick={() => { setMode(example.mode); setQuestion(example.title); input.current?.focus() }}><strong className="example-full">{example.title}</strong><b className="example-short">{example.short}</b><span>{example.sub}</span><ArrowUpRight size={16} /></button>)}</div></div>}
      {loading && <p role="status" className="muted-copy py-10">正在恢复研究上下文…</p>}
      <div className="research-turns">{runs.map(run => <Run key={run.id} run={run} busy={running || loading} onRetry={retryRun} />)}</div>
      {error && <ErrorState className="py-4" message={error} onRetry={() => { activeId.current = null; setReload(x => x + 1) }} />}
      {notice && <p role="status" className="research-notice">{notice}</p>}
      <form className="research-composer" onSubmit={submit}>
        <fieldset disabled={running || loading}>
          <div className="research-modes" role="group" aria-label="研究任务">{MODES.map(m => <button type="button" key={m.id} className={mode === m.id ? 'is-active' : ''} aria-pressed={mode === m.id} onClick={() => setMode(m.id)}>{m.label}</button>)}</div>
          <div className="research-scope"><div className="scope-label">研究范围 <span>最多 3 件</span></div>{selected.length > 0 && <div className="scope-items">{selected.map(item => <span key={item.id}>{item.item_name}<button type="button" aria-label={`移除研究范围：${item.item_name}`} onClick={() => setSelected(old => old.filter(i => i.id !== item.id))}><X size={12} /></button></span>)}</div>}{selected.length < 3 && <SearchBar label="添加研究饰品" placeholder={mode === 'knowledge' ? '可选：添加饰品作为上下文…' : '搜索并添加饰品…'} onSelect={choose} />}</div>
          {mode === 'rental' && <div className="research-rental-fields"><label>使用天数<input aria-label="研究使用天数" type="number" min="1" max="365" required value={days} onChange={e => setDays(e.target.value)} /></label><label>预算（元）<input aria-label="研究预算" type="number" min="0" max="1000000000" step="0.01" required value={budget} onChange={e => setBudget(e.target.value)} /></label></div>}
          <label className="sr-only" htmlFor="research-goal">研究目标或追问</label><textarea id="research-goal" ref={input} value={question} onChange={e => setQuestion(e.target.value)} maxLength={2000} required rows={3} placeholder={runs.length ? '继续追问，保留当前饰品与研究上下文…' : '例如：先核对红线的真实报价，再看看近期公告与风险。'} />
        </fieldset>
        <div className="research-composer-footer"><label><input type="checkbox" checked={refresh} onChange={e => setRefresh(e.target.checked)} disabled={running} />更新行情与公告</label><span>{question.length}/2000</span>{busy ? <Button onClick={() => abort.current?.abort()}><Stop size={16} />停止</Button> : <Button type="submit" variant="primary" disabled={running || loading || !question.trim()}><ArrowUp size={17} />{runs.length ? '继续研究' : '开始研究'}</Button>}</div>
      </form>
      <p className="research-footnote">{service?.model?.configured ? '结论基于本轮证据生成，请核对引用与数据时间。' : 'AI 模型尚未连接。行情、公告、检索和研究记录可独立使用。'}</p>
    </div>
    <aside className="research-connections"><h2>研究如何完成</h2><ol><li><b>01</b><div><strong>核对真实数据</strong><p>只更新你选中的饰品，保留来源与时间。</p></div></li><li><b>02</b><div><strong>关联公告与知识</strong><p>把市场事实、背景资料和假设分开。</p></div></li><li><b>03</b><div><strong>形成可回看的产物</strong><p>每轮保存证据与结果，支持继续追问。</p></div></li></ol><h2 className="mt-7">数据连接</h2>{service?.sources?.map(source => <details key={source.id}><summary><span>{source.label}</span><small className={source.status === 'demo' || source.status === 'not_configured' ? 'is-limited' : ''}>{{ available: '可调用', configured: '已配置', not_configured: '未配置', demo: '演示' }[source.status]}</small></summary><p>{source.detail}</p></details>)}<p className="research-connection-note">连接状态表示配置情况；每次调用结果在研究过程里单独核验。</p></aside>
  </div>
}
