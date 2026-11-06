export default function Skeleton({ w = '100%', h = 12, className = '', radius = 4 }) {
  return (
    <div aria-hidden="true"
      className={`bg-[var(--border-default)] ${className}`}
      style={{ width: w, height: h, borderRadius: radius, animation: 'pulse 1.6s ease infinite' }}
    />
  )
}
