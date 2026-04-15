import { useState, useRef } from 'react'

const BASE_URL = 'http://localhost:8000/api'

const SUGGESTED = [
  '龙狙为什么最近波动这么大？',
  '刀应该租还是买？怎么算更划算？',
  '赛事期间皮肤价格有什么规律？',
  '什么稀有度的皮肤最值得投资？',
  '开箱和直接购买哪个更划算？',
  'StatTrak 版本值得溢价买吗？',
]

const CATEGORY_LABEL = {
  rent_vs_buy: '租 vs 买',
  tournament_effects: '赛事影响',
  price_factors: '价格因素',
  rarity_guide: '稀有度',
  specific_skins: '皮肤分析',
  skin_investment: '投资策略',
  market_mechanics: '市场机制',
  platform_comparison: '平台对比',
}

function SourceTag({ source }) {
  const label = CATEGORY_LABEL[source.category] || source.category
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: 'rgba(74,142,245,0.08)',
      border: '1px solid rgba(74,142,245,0.2)',
      borderRadius: 6, padding: '3px 9px',
      fontSize: 11, color: '#7eb3ff',
    }}>
      <span style={{ opacity: 0.5, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </span>
      <span style={{ fontWeight: 600 }}>{source.title}</span>
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

    // Reset state
    setAnswer('')
    setSources([])
    setError('')
    setLoading(true)

    // Abort previous request if any
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
        buf = lines.pop()  // keep incomplete line

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
    <div style={{
      background: 'linear-gradient(145deg, #0f1520 0%, #0d1320 100%)',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: 16, padding: '28px 28px 24px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'linear-gradient(135deg, #4a8ef5, #8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 15, flexShrink: 0,
        }}>◎</div>
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: 'white', lineHeight: 1 }}>
            Ask Sense
          </h2>
          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 3 }}>
            基于知识库的 CS2 市场问答 · RAG 检索增强
          </p>
        </div>
      </div>

      {/* Suggested questions */}
      {!hasResult && !loading && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginBottom: 18 }}>
          {SUGGESTED.map(s => (
            <button
              key={s}
              onClick={() => submit(s)}
              style={{
                fontSize: 11, color: 'var(--text-secondary)',
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 6, padding: '5px 11px',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'rgba(74,142,245,0.3)'
                e.currentTarget.style.color = '#7eb3ff'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                e.currentTarget.style.color = 'var(--text-secondary)'
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div style={{ display: 'flex', gap: 10 }}>
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submit()}
          placeholder="问任何关于 CS2 饰品市场的问题…"
          disabled={loading}
          style={{
            flex: 1, background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 9, padding: '11px 14px',
            color: 'var(--text-primary)', fontSize: 13, outline: 'none',
            transition: 'border-color 0.15s',
          }}
          onFocus={e => e.target.style.borderColor = 'rgba(74,142,245,0.4)'}
          onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
        />
        <button
          onClick={() => submit()}
          disabled={loading || !question.trim()}
          style={{
            background: loading || !question.trim()
              ? 'rgba(74,142,245,0.2)'
              : 'linear-gradient(135deg, #4a8ef5, #6366f1)',
            border: 'none', borderRadius: 9, padding: '11px 20px',
            color: loading || !question.trim() ? 'rgba(255,255,255,0.3)' : 'white',
            fontSize: 13, fontWeight: 600, cursor: loading || !question.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s', flexShrink: 0,
          }}
        >
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <span className="typing-dot" style={{ display: 'inline-block', width: 5, height: 5, borderRadius: '50%', background: 'rgba(255,255,255,0.5)' }} />
              <span className="typing-dot" style={{ display: 'inline-block', width: 5, height: 5, borderRadius: '50%', background: 'rgba(255,255,255,0.5)' }} />
              <span className="typing-dot" style={{ display: 'inline-block', width: 5, height: 5, borderRadius: '50%', background: 'rgba(255,255,255,0.5)' }} />
            </span>
          ) : '提问'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          marginTop: 14, padding: '10px 14px', borderRadius: 8,
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          color: '#fca5a5', fontSize: 12,
        }}>
          {error}
        </div>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 7, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            参考知识片段
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {sources.map(s => <SourceTag key={s.id} source={s} />)}
          </div>
        </div>
      )}

      {/* Answer */}
      {answer && (
        <div style={{
          marginTop: 16, padding: '16px 18px',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 10,
        }}>
          <p style={{
            fontSize: 13, color: 'var(--text-primary)',
            lineHeight: 1.8, whiteSpace: 'pre-wrap',
          }}>
            {answer}
          </p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !answer && (
        <div style={{ marginTop: 16 }}>
          {[100, 85, 70].map((w, i) => (
            <div key={i} style={{
              height: 12, width: `${w}%`,
              background: 'rgba(255,255,255,0.05)',
              borderRadius: 4, marginBottom: 10,
              animation: 'pulse 1.6s ease infinite',
              animationDelay: `${i * 0.15}s`,
            }} />
          ))}
        </div>
      )}

      {/* Reset */}
      {hasResult && !loading && (
        <button
          onClick={() => { setAnswer(''); setSources([]); setQuestion(''); setError('') }}
          style={{
            marginTop: 14, fontSize: 11, color: 'var(--text-dim)',
            background: 'transparent', border: 'none', cursor: 'pointer', padding: 0,
          }}
        >
          ← 清空，重新提问
        </button>
      )}
    </div>
  )
}
