import { formatCNY } from '../utils/formatters'
import { PLATFORM_COLORS } from '../utils/constants'

export default function PlatformComparisonTable({ platforms = [] }) {
  if (!platforms.length) {
    return (
      <p style={{ color: 'var(--text-dim)', fontSize: 13, textAlign: 'center', padding: '12px 0' }}>
        暂无平台对比数据
      </p>
    )
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            {['平台', '当前价格', '7日均价', '买卖价差', '流动性', '溢价'].map(h => (
              <th
                key={h}
                style={{
                  padding: '8px 12px',
                  textAlign: h === '平台' ? 'left' : 'right',
                  color: 'var(--text-dim)',
                  fontWeight: 500,
                  fontSize: 11,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  whiteSpace: 'nowrap',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {platforms.map((p, i) => (
            <tr
              key={p.platform}
              style={{
                borderBottom: i < platforms.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                background: p.is_best_price ? 'rgba(74,142,245,0.05)' : 'transparent',
              }}
            >
              <td style={{ padding: '10px 12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      background: PLATFORM_COLORS[p.platform] || '#4a8ef5',
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{p.platform}</span>
                  {p.is_best_price && (
                    <span
                      style={{
                        fontSize: 10,
                        background: 'rgba(74,142,245,0.15)',
                        color: '#4a8ef5',
                        border: '1px solid rgba(74,142,245,0.3)',
                        borderRadius: 4,
                        padding: '1px 5px',
                      }}
                    >
                      最优
                    </span>
                  )}
                  {p.supports_rental && (
                    <span
                      style={{
                        fontSize: 10,
                        background: 'rgba(168,85,247,0.12)',
                        color: '#a855f7',
                        border: '1px solid rgba(168,85,247,0.25)',
                        borderRadius: 4,
                        padding: '1px 5px',
                      }}
                    >
                      租赁
                    </span>
                  )}
                </div>
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 700, color: 'var(--price)' }}>
                {formatCNY(p.current_price)}
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                {formatCNY(p.avg_7d)}
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                {formatCNY(p.spread)}
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                <span
                  style={{
                    color:
                      p.liquidity_score == null ? 'var(--text-dim)' :
                      p.liquidity_score > 60 ? '#4caf50' :
                      p.liquidity_score < 40 ? '#f44336' : '#f5a623',
                    fontWeight: 600,
                  }}
                >
                  {p.liquidity_score != null ? p.liquidity_score.toFixed(0) : '—'}
                </span>
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                <span
                  style={{
                    color: p.price_vs_best_pct > 0 ? '#f97316' : 'var(--text-dim)',
                    fontWeight: p.price_vs_best_pct > 0 ? 600 : 400,
                  }}
                >
                  {p.price_vs_best_pct != null
                    ? p.price_vs_best_pct === 0 ? '基准' : `+${p.price_vs_best_pct.toFixed(1)}%`
                    : '—'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
