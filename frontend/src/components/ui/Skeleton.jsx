export default function Skeleton({ w = '100%', h = 12, className = '', radius = 4 }) {
  return (
    <div
      className={`bg-white/[0.05] ${className}`}
      style={{ width: w, height: h, borderRadius: radius, animation: 'pulse 1.6s ease infinite' }}
    />
  )
}
