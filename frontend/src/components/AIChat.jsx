import { useState, useRef, useEffect } from 'react'

const BASE_URL = 'http://localhost:8000/api'

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
  '这个皮肤稀不稀有？',
]

export default function AIChat({ itemId, itemName }) {
  const [history, setHistory] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
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

    const newHistory = [...history, { role: 'user', content: msg }]
    setHistory(newHistory)

    let full = ''
    try {
      for await (const chunk of streamChat(itemId, msg, history)) {
        full += chunk
        setStreamingText(full)
      }
    } catch (err) {
      full = `连接失败，请稍后重试。`
      setStreamingText(full)
    }

    setHistory([...newHistory, { role: 'assistant', content: full }])
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
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: 400,
        background: 'rgba(14,17,23,0.6)',
        borderRadius: 12,
        border: '1px solid rgba(255,255,255,0.07)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 8, height: 8, borderRadius: '50%',
            background: '#4a8ef5',
            boxShadow: '0 0 8px rgba(74,142,245,0.6)',
          }}
          className="live-dot"
        />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>AI 分析师</span>
        <span style={{ fontSize: 11, color: 'var(--text-dim)', marginLeft: 'auto' }}>
          Claude · {itemName || '当前饰品'}
        </span>
      </div>

      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        {/* Empty state / quick questions */}
        {showQuickQuestions && (
          <div>
            <p style={{ fontSize: 12, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 16 }}>
              基于实时市场数据，向 AI 提问关于这个饰品的任何问题
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {QUICK_QUESTIONS.map(q => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  style={{
                    textAlign: 'left',
                    padding: '8px 12px',
                    background: 'rgba(74,142,245,0.06)',
                    border: '1px solid rgba(74,142,245,0.15)',
                    borderRadius: 8,
                    color: 'rgba(255,255,255,0.6)',
                    fontSize: 12,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={e => {
                    e.target.style.background = 'rgba(74,142,245,0.12)'
                    e.target.style.color = 'rgba(255,255,255,0.85)'
                  }}
                  onMouseLeave={e => {
                    e.target.style.background = 'rgba(74,142,245,0.06)'
                    e.target.style.color = 'rgba(255,255,255,0.6)'
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message history */}
        {history.map((msg, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {msg.role === 'user' ? (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div
                  className="chat-bubble-user"
                  style={{ maxWidth: '82%', padding: '8px 12px', fontSize: 13, lineHeight: 1.5 }}
                >
                  {msg.content}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  className="chat-bubble-ai"
                  style={{
                    maxWidth: '92%',
                    padding: '10px 14px',
                    fontSize: 13,
                    lineHeight: 1.65,
                    color: 'var(--text-primary)',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Streaming response */}
        {streaming && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              className="chat-bubble-ai"
              style={{
                maxWidth: '92%',
                padding: '10px 14px',
                fontSize: 13,
                lineHeight: 1.65,
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
              }}
            >
              {streamingText || (
                <span style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '2px 0' }}>
                  <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: '#4a8ef5', display: 'inline-block' }} />
                  <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: '#4a8ef5', display: 'inline-block' }} />
                  <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: '#4a8ef5', display: 'inline-block' }} />
                </span>
              )}
              {streamingText && <span style={{ opacity: 0.5 }}>▌</span>}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: '12px 16px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
          display: 'flex',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={streaming}
          placeholder="问问 AI 关于这个饰品…"
          style={{
            flex: 1,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.09)',
            borderRadius: 8,
            padding: '8px 12px',
            fontSize: 13,
            color: 'var(--text-primary)',
            outline: 'none',
            transition: 'border-color 0.15s ease',
          }}
          onFocus={e => e.target.style.borderColor = 'rgba(74,142,245,0.4)'}
          onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.09)'}
        />
        <button
          onClick={() => send()}
          disabled={streaming || !input.trim()}
          style={{
            padding: '8px 14px',
            background: streaming || !input.trim() ? 'rgba(74,142,245,0.2)' : '#4a8ef5',
            border: 'none',
            borderRadius: 8,
            color: streaming || !input.trim() ? 'rgba(255,255,255,0.3)' : 'white',
            fontSize: 13,
            fontWeight: 600,
            cursor: streaming || !input.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s ease',
            flexShrink: 0,
          }}
        >
          发送
        </button>
      </div>
    </div>
  )
}
