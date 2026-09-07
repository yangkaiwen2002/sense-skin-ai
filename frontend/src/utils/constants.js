// ── CS2 rarity — the real in-game color convention. This is meaningful DATA
// color (identifies an item's tier) and must never be reused as decorative UI
// chrome elsewhere in the app.
export const RARITY_COLOR = {
  '违禁': '#e4ae39',
  '隐秘': '#eb4b4b',
  '保密': '#d32ce6',
  '受限': '#8847ff',
  '军规': '#4b69ff',
  '精工': '#5e98d9',
  '消费级': '#b0c3d9',
}

export const RARITY_CLASS = {
  '违禁': 'rarity-contraband',
  '隐秘': 'rarity-covert',
  '保密': 'rarity-classified',
  '受限': 'rarity-restricted',
  '军规': 'rarity-milspec',
  '精工': 'rarity-industrial',
}

export const WEAPON_ABBR = {
  '步枪': 'AR', '狙击枪': 'SNP', '手枪': 'PST', '刀': 'KNF',
  '霰弹枪': 'SHT', '冲锋枪': 'SMG', '机枪': 'MG', '手套': 'GLV',
}

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

// Platform identity colors — categorical, one per real external platform,
// used only as small identifier dots (not decoration).
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

// Event-type accents, kept out of the purple family (purple is reserved
// for nothing here — CS2 rarity "restricted" already owns that hue).
export const EVENT_TYPE_COLORS = {
  game_update: { dot: 'bg-red-400', text: 'text-red-300', bg: 'bg-red-900/20 border-red-800/40' },
  major_event: { dot: 'bg-blue-400', text: 'text-blue-300', bg: 'bg-blue-900/20 border-blue-800/40' },
  tournament: { dot: 'bg-amber-400', text: 'text-amber-300', bg: 'bg-amber-900/20 border-amber-800/40' },
  holiday: { dot: 'bg-green-400', text: 'text-green-300', bg: 'bg-green-900/20 border-green-800/40' },
  platform_promo: { dot: 'bg-slate-400', text: 'text-slate-300', bg: 'bg-slate-800/40 border-slate-700/50' },
}
