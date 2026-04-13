export const MOCK_ITEMS = [
  { id: 1, item_name: 'AK-47 | 红线 (久经沙场)' },
  { id: 2, item_name: '爪子刀 | 多普勒 (崭新出厂)' },
  { id: 3, item_name: 'M4A1 消音型 | 印花集 (崭新出厂)' },
]

export const MOCK_OVERVIEW = {
  item_id: 1,
  item_name: 'AK-47 | 红线 (久经沙场)',
  rarity: '精工',
  exterior: '久经沙场',
  stattrak: false,
  platforms: [
    {
      platform: 'BUFF',
      platform_id: 1,
      current_price: 356.5,
      avg_7d: 349.2,
      avg_30d: 340.8,
      return_7d: 0.021,
      volatility_7d: 0.061,
      spread: 6.8,
      liquidity_score: 78,
      risk_labels: ['Potential Overheat'],
    },
  ],
}
