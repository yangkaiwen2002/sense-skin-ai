import { useState, useRef } from 'react'
import { BookOpen, PaperPlaneRight } from '@phosphor-icons/react'
import { BASE_URL } from '../services/api'
import Button from './ui/Button'
import Skeleton from './ui/Skeleton'

const SUGGESTED = [
  '龙狙为什么最近波动这么大？',
  '刀应该租还是买？怎么算更划算？',
  '赛事期间皮肤价格有什么规律？',
  '什么稀有度的皮肤最值得投资？',
  '开箱和直接购买哪个更划算？',
  'StatTrak 版本值得溢价买吗？',
]

const CATEGORY_LABEL = {
  rent_vs_buy: '租 vs 买', tournament_effects: '赛事影响', price_factors: '价格因素',
  rarity_guide: '稀有度', specific_skins: '皮肤分析', skin_investment: '投资策略',
  market_mechanics: '市场机制', platform_comparison: '平台对比',
}

function SourceTag({ source }) {
  const label = CATEGORY_LABEL[source.category] || source.category
  return (
    <div className="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] px-2.5 py-1 text-[11px]"
      style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent-border)', color: 'var(--accent-strong)' }}>
      <span className="opacity-50 text-[9px] uppercase tracking-wide">{label}</span>
      <span className="font-semibold">{source.title}</span>
    </div>
  )
}

export default function AskSense() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const abortRef = useRef(null)

  async function submit(q) {
    const text = (q ?? question).trim()
    if (!text) return
    if (q) setQuestion(q)

    setAnswer('')
    setSources([])
    setError('')
    setLoading(true)

    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    try {
      const res = await fetch(`${BASE_URL}/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, top_k: 3 }),
        signal: ctrl.signal,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6)
          if (raw === '[DONE]') { setLoading(false); return }
          try {
            const evt = JSON.parse(raw)
            if (evt.type === 'sources') setSources(evt.sources)
            else if (evt.type === 'text') setAnswer(a => a + evt.text)
            else if (evt.type === 'error') setError(evt.error)
          } catch { /* ignore malformed lines */ }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') setError(e.message || '请求失败，请检查后端是否运行')
    } finally {
      setLoading(false)
    }
  }

  const hasResult = answer || sources.length > 0

  return (
    <div className="surface-card p-5 sm:p-6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-[var(--radius-sm)] flex items-center justify-center shrink-0" style={{ background: 'var(--accent-soft)', border: '1px solid var(--accent-border)' }}>
          <BookOpen size={16} weight="bold" style={{ color: 'var(--accent-strong)' }} />
        </div>
        <div>
          <h2 className="text-base font-bold text-[var(--text-primary)] leading-none">Ask Sense</h2>
          <p className="text-[11px] text-[var(--text-dim)] mt-0.5">基于知识库的 CS2 市场问答 · RAG 检索增强</p>
        </div>
      </div>

      {!hasResult && !loading && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {SUGGESTED.map(s => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="text-[11px] text-[var(--text-secondary)] bg-white/[0.04] border border-[var(--border-subtle)] rounded-[var(--radius-sm)] px-2.5 py-1.5
                transition-colors duration-150 hover:border-[var(--accent-border)] hover:text-[var(--accent-strong)]"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submit()}
          placeholder="问任何关于 CS2 饰品市场的问题…"
          disabled={loading}
          className="flex-1 min-w-0 min-h-[44px] bg-white/[0.05] border border-[var(--border-default)] rounded-[var(--radius-sm)]
            px-3.5 py-2.5 text-[13px] text-[var(--text-primary)] outline-none transition-colors duration-150
            focus:border-[var(--accent-border)] placeholder:text-[var(--text-dim)]"
        />
        <Button variant="primary" onClick={() => submit()} disabled={loading || !question.trim()} loading={loading} className="shrink-0">
          {!loading && <PaperPlaneRight size={14} weight="bold" />}
          提问
        </Button>
      </div>

      {error && (
        <div className="mt-3.5 px-3.5 py-2.5 rounded-[var(--radius-sm)] text-xs" style={{ background: 'var(--avoid-soft)', border: '1px solid rgba(229,72,77,0.25)', color: '#f5a3a6' }}>
          {error}
        </div>
      )}

      {sources.length > 0 && (
        <div className="mt-4">
          <p className="text-[10px] text-[var(--text-dim)] mb-1.5 uppercase tracking-wide">参考知识片段</p>
          <div className="flex flex-wrap gap-1.5">
            {sources.map(s => <SourceTag key={s.id} source={s} />)}
          </div>
        </div>
      )}

      {answer && (
        <div className="mt-4 px-4 py-3.5 rounded-[var(--radius-sm)] bg-white/[0.03] border border-[var(--border-subtle)]">
          <p className="text-[13px] text-[var(--text-primary)] leading-[1.8] whitespace-pre-wrap">{answer}</p>
        </div>
      )}

      {loading && !answer && (
        <div className="mt-4 space-y-2.5">
          <Skeleton w="100%" h={12} />
          <Skeleton w="85%" h={12} />
          <Skeleton w="70%" h={12} />
        </div>
      )}

      {hasResult && !loading && (
        <button
          onClick={() => { setAnswer(''); setSources([]); setQuestion(''); setError('') }}
          className="mt-3.5 text-[11px] text-[var(--text-dim)] hover:text-[var(--text-secondary)] transition-colors"
        >
          ← 清空，重新提问
        </button>
      )}
    </div>
  )
}
