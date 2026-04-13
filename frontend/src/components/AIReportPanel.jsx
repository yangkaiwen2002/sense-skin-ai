import { useState } from 'react'
import { generateAIReport } from '../services/api'

export default function AIReportPanel({ itemId }) {
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  async function handleGenerate() {
    setLoading(true)
    setError(null)
    const data = await generateAIReport(itemId)
    setLoading(false)
    if (data) {
      setReport(data)
    } else {
      setError('生成失败，请稍后重试')
    }
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-cyan-400" />
          </div>
          <p className="text-sm font-semibold text-white">AI 市场分析</p>
        </div>
        {report && (
          <span className="text-slate-500 text-xs">
            {new Date(report.generated_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      {!report && !loading && (
        <div className="text-center py-6">
          <p className="text-slate-500 text-xs mb-4">
            基于当前市场数据和事件背景，由 Claude AI 生成分析报告
          </p>
          <button
            onClick={handleGenerate}
            className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
          >
            生成 AI 分析
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8 gap-3">
          <div className="w-5 h-5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
          <span className="text-slate-400 text-sm">正在分析市场数据...</span>
        </div>
      )}

      {error && (
        <div className="text-center py-4">
          <p className="text-red-400 text-sm mb-3">{error}</p>
          <button onClick={handleGenerate} className="text-cyan-400 text-xs hover:text-cyan-300 underline">
            重试
          </button>
        </div>
      )}

      {report && (
        <div>
          <div className="bg-slate-900/50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">{report.report_text}</p>
          </div>
          <button
            onClick={handleGenerate}
            className="mt-3 text-xs text-slate-500 hover:text-slate-400 transition-colors"
          >
            重新生成
          </button>
        </div>
      )}
    </div>
  )
}
