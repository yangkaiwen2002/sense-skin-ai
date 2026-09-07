import { useState, useRef, useEffect } from 'react'
import { PaperPlaneRight, Circle } from '@phosphor-icons/react'
import { BASE_URL } from '../services/api'

async function* streamChat(itemId, message, history) {
  const res = await fetch(`${BASE_URL}/items/${itemId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })

  if (!res.ok) {
    yield `[错误] 请求失败 (${res.status})`
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6).trim()
      if (data === '[DONE]') return
      try {
        const parsed = JSON.parse(data)
        if (parsed.text) yield parsed.text
        if (parsed.error) yield `[错误] ${parsed.error}`
      } catch {
        // ignore parse errors
      }
    }
  }
}

const QUICK_QUESTIONS = [
  '现在值得买吗？',
  '未来价格走势如何？',
  '同价位有更好的推荐吗？',
]

export default function AIChat({ itemId, itemName }) {
  const [history, setHistory] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [chatError, setChatError] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, streamingText])

  async function send(question) {
    const msg = question || input.trim()
    if (!msg || streaming) return
    setInput('')
    setStreaming(true)
    setStreamingText('')
    setChatError(false)

    const newHistory = [...history, { role: 'user', content: msg }]
    setHistory(newHistory)

    let full = ''
    let failed = false
    try {
      for await (const chunk of streamChat(itemId, msg, history)) {
        if (chunk.startsWith('[错误]')) failed = true
        full += chunk
        setStreamingText(full)
      }
    } catch {
      full = '连接失败，请稍后重试。'
      failed = true
      setStreamingText(full)
    }

    setHistory([...newHistory, { role: 'assistant', content: full, error: failed }])
    setStreamingText('')
    setStreaming(false)
    inputRef.current?.focus()
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const showQuickQuestions = history.length === 0 && !streaming

  return (
    <div className="flex flex-col h-full min-h-[340px]">
      {/* Header */}
      <div className="px-4 py-2.5 border-b border-[var(--border-subtle)] flex items-center gap-2 shrink-0">
        <Circle size={7} weight="fill" className="glow-pulse" style={{ color: 'var(--accent)' }} />
        <span className="text-xs font-semibold text-[var(--text-primary)]">AI 分析师</span>
        <span className="text-[10px] text-[var(--text-dim)] ml-auto truncate max-w-[120px]">Claude · {itemName || '当前饰品'}</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3.5 flex flex-col gap-2.5">
        {showQuickQuestions && (
          <div>
            <p className="text-[11px] text-[var(--text-dim)] text-center mb-3 leading-relaxed">
              基于实时市场数据，向 AI 提问关于这个饰品的问题
            </p>
            <div className="flex flex-col gap-1.5">
              {QUICK_QUESTIONS.map(q => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-left px-3 py-2 rounded-[var(--radius-sm)] text-xs transition-colors duration-150
                    bg-[var(--accent-soft)] border border-[var(--accent-border)] text-white/60 hover:text-white/85 hover:bg-[var(--accent-soft)]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {history.map((msg, i) => (
          <div key={i} className="flex flex-col gap-0.5">
            {msg.role === 'user' ? (
              <div className="flex justify-end">
                <div className="chat-bubble-user max-w-[82%] px-3 py-2 text-[13px] leading-relaxed">{msg.content}</div>
              </div>
            ) : (
              <div className="flex justify-start">
                <div
                  className="chat-bubble-ai max-w-[92%] px-3.5 py-2.5 text-[13px] leading-[1.65] whitespace-pre-wrap"
                  style={{ color: msg.error ? 'var(--avoid)' : 'var(--text-primary)' }}
                >
                  {msg.content}
                </div>
              </div>
            )}
          </div>
        ))}

        {streaming && (
          <div className="flex justify-start">
            <div className="chat-bubble-ai max-w-[92%] px-3.5 py-2.5 text-[13px] leading-[1.65] text-[var(--text-primary)] whitespace-pre-wrap">
              {streamingText || (
                <span className="flex gap-1 items-center py-0.5">
                  <span className="typing-dot w-1.5 h-1.5 rounded-full inline-block" style={{ background: 'var(--accent)' }} />
                  <span className="typing-dot w-1.5 h-1.5 rounded-full inline-block" style={{ background: 'var(--accent)' }} />
                  <span className="typing-dot w-1.5 h-1.5 rounded-full inline-block" style={{ background: 'var(--accent)' }} />
                </span>
              )}
              {streamingText && <span className="opacity-50">▌</span>}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3.5 py-3 border-t border-[var(--border-subtle)] flex gap-2 shrink-0">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={streaming}
          placeholder="问问 AI 关于这个饰品…"
          className="flex-1 min-w-0 bg-white/[0.05] border border-[var(--border-default)] rounded-[var(--radius-sm)]
            px-3 py-2 text-[13px] text-[var(--text-primary)] outline-none transition-colors duration-150
            focus:border-[var(--accent-border)] placeholder:text-[var(--text-dim)]"
        />
        <button
          onClick={() => send()}
          disabled={streaming || !input.trim()}
          aria-label="发送"
          className="shrink-0 w-10 h-10 flex items-center justify-center rounded-[var(--radius-sm)] transition-colors duration-150
            disabled:cursor-not-allowed active:scale-95"
          style={{
            background: streaming || !input.trim() ? 'var(--accent-soft)' : 'var(--accent)',
            color: streaming || !input.trim() ? 'rgba(255,255,255,0.3)' : 'white',
          }}
        >
          <PaperPlaneRight size={16} weight="fill" />
        </button>
      </div>
    </div>
  )
}
