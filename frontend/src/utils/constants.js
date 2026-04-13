export const RISK_COLORS = {
  'High Volatility': { bg: 'bg-red-900/40', border: 'border-red-700/60', text: 'text-red-300', dot: 'bg-red-400' },
  'Low Liquidity': { bg: 'bg-orange-900/40', border: 'border-orange-700/60', text: 'text-orange-300', dot: 'bg-orange-400' },
  'Potential Overheat': { bg: 'bg-yellow-900/40', border: 'border-yellow-700/60', text: 'text-yellow-300', dot: 'bg-yellow-400' },
  'Stable': { bg: 'bg-green-900/40', border: 'border-green-700/60', text: 'text-green-300', dot: 'bg-green-400' },
}

export const RISK_LABELS_ZH = {
  'High Volatility': '高波动',
  'Low Liquidity': '低流动性',
  'Potential Overheat': '可能过热',
  'Stable': '价格稳定',
}

export const PLATFORM_COLORS = {
  'BUFF': '#e85d04',
  'Steam': '#66c0f4',
  '悠悠有品': '#a855f7',
  'IGXE': '#22c55e',
}

export const EVENT_TYPE_LABELS = {
  game_update: '游戏更新',
  major_event: 'Major 赛事',
  tournament: '锦标赛 · HLTV',
  holiday: '节假日',
  platform_promo: '平台活动',
}

export const EVENT_TYPE_COLORS = {
  game_update: { dot: 'bg-red-400', text: 'text-red-300', bg: 'bg-red-900/20 border-red-800/40' },
  major_event: { dot: 'bg-blue-400', text: 'text-blue-300', bg: 'bg-blue-900/20 border-blue-800/40' },
  tournament: { dot: 'bg-yellow-400', text: 'text-yellow-300', bg: 'bg-yellow-900/20 border-yellow-800/40' },
  holiday: { dot: 'bg-green-400', text: 'text-green-300', bg: 'bg-green-900/20 border-green-800/40' },
  platform_promo: { dot: 'bg-purple-400', text: 'text-purple-300', bg: 'bg-purple-900/20 border-purple-800/40' },
}
