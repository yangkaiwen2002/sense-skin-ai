import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'
import { formatCNY, formatDate } from '../utils/formatters'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null
  return (
    <div style={{ background: 'var(--bg-surface-raised)', border: '1px solid var(--border-default)', borderRadius: 8, padding: '8px 12px', boxShadow: 'var(--shadow-md)' }}>
      <p style={{ color: 'var(--text-dim)', fontSize: 11, marginBottom: 4 }}>{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} className="font-tabular" style={{ fontSize: 13, fontWeight: 600, color: p.color }}>
          {p.name}: {formatCNY(p.value)}
        </p>
      ))}
    </div>
  )
}

export default function TrendChart({ data = [], avg7d, avg30d }) {
  if (!data.length) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
        <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>暂无历史价格数据</p>
      </div>
    )
  }

  const formatted = data.map(d => ({ ...d, date: formatDate(d.date) }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={formatted} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.12)' }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={v => `¥${v}`}
            width={70}
          />
          <Tooltip content={<CustomTooltip />} />
          {avg7d && (
            <ReferenceLine
              y={avg7d}
              stroke="#E5A93B"
              strokeDasharray="5 3"
              label={{ value: '7日均', fill: '#E5A93B', fontSize: 10, position: 'right' }}
            />
          )}
          {avg30d && (
            <ReferenceLine
              y={avg30d}
              stroke="#6b7280"
              strokeDasharray="5 3"
              label={{ value: '30日均', fill: '#6b7280', fontSize: 10, position: 'right' }}
            />
          )}
          <Line
            type="monotone"
            dataKey="price"
            name="价格"
            stroke="#4472FF"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#4472FF' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
