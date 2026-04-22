const BASE_URL = 'http://localhost:8000/api'

async function request(path, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export const getItems = (limit = 50) => request(`/items?limit=${limit}`)
export const searchItems = (q) => request(`/items/search?q=${encodeURIComponent(q)}`)
export const getItemOverview = (id) => request(`/items/${id}/overview`)
export const getItemHistory = (id, days = 30, platform = '') =>
  request(`/items/${id}/history?days=${days}${platform ? `&platform=${platform}` : ''}`)
export const getItemCompare = (id) => request(`/items/${id}/compare`)
export const getItemEvents = (id, days = 30) => request(`/items/${id}/events?days=${days}`)
export const getEventAwareAnalysis = (id) => request(`/items/${id}/event-aware-analysis`)
export const rentVsBuy = (id, body) =>
  request(`/items/${id}/rent-vs-buy`, { method: 'POST', body: JSON.stringify(body) })
export const generateAIReport = (id) =>
  request(`/items/${id}/ai-report`, { method: 'POST' })
export const seedDatabase = () => request('/seed', { method: 'POST' })
export const refreshPrices = () =>
  fetch(`${BASE_URL}/refresh-prices`, { method: 'POST' })
    .then(r => r.ok ? r.json() : null)
    .catch(() => null)

// ── Scoring & intelligence ──────────────────────────────────────────────────
export const getItemScore     = (id)          => request(`/items/${id}/score`)
export const getItemDecision  = (id)          => request(`/items/${id}/decision`)
export const getOpportunities = (limit = 8)   => request(`/opportunities?limit=${limit}`)
export const getMarketSummary = ()            => request('/market-summary')
export const getMarketEvents  = ()            => request('/market/events')
