export function formatCNY(value) {
  if (value == null) return '—'
  return `¥${Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function formatPercent(value) {
  if (value == null) return '—'
  const pct = (value * 100).toFixed(2)
  return value >= 0 ? `+${pct}%` : `${pct}%`
}

export function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

export function formatDateFull(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${String(d.getMonth() + 1).padStart(2, '0')}月${String(d.getDate()).padStart(2, '0')}日`
}

export function getRarityColor(rarity) {
  const map = {
    '违禁': 'text-red-400',
    '隐秘': 'text-pink-400',
    '保密': 'text-purple-400',
    '受限': 'text-blue-400',
    '工业级': 'text-sky-400',
    '消费级': 'text-gray-400',
    '精工': 'text-yellow-400',
  }
  return map[rarity] || 'text-slate-400'
}

export function getRarityBg(rarity) {
  const map = {
    '违禁': 'bg-red-900/30 border-red-700/50 text-red-300',
    '隐秘': 'bg-pink-900/30 border-pink-700/50 text-pink-300',
    '保密': 'bg-purple-900/30 border-purple-700/50 text-purple-300',
    '受限': 'bg-blue-900/30 border-blue-700/50 text-blue-300',
    '精工': 'bg-yellow-900/30 border-yellow-700/50 text-yellow-300',
  }
  return map[rarity] || 'bg-slate-800 border-slate-600 text-slate-300'
}
