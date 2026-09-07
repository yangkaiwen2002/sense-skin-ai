import { WarningCircle } from '@phosphor-icons/react'
import Button from './Button'

export default function ErrorState({ message = '加载失败，请稍后重试', onRetry, retryLabel = '重试', className = '' }) {
  return (
    <div className={`text-center py-14 px-6 ${className}`}>
      <div className="w-11 h-11 rounded-full bg-[var(--avoid-soft)] border border-[var(--avoid)]/30 flex items-center justify-center mx-auto mb-4">
        <WarningCircle size={20} weight="regular" style={{ color: 'var(--avoid)' }} />
      </div>
      <p className="text-sm text-[var(--text-secondary)] mb-5">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>{retryLabel}</Button>
      )}
    </div>
  )
}
