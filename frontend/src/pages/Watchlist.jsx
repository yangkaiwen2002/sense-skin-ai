import { useNavigate } from 'react-router-dom'
import { CaretRight, Star } from '@phosphor-icons/react'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'

export default function Watchlist() {
  const navigate = useNavigate()
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-1.5 text-xs text-[var(--text-dim)] mb-5">
        <button onClick={() => navigate('/')} className="hover:text-[var(--text-secondary)] transition-colors">首页</button>
        <CaretRight size={11} />
        <span className="text-[var(--text-secondary)]">我的关注</span>
      </div>

      <EmptyState
        icon={Star}
        title="关注列表"
        sub="收藏你关注的饰品，快速追踪价格变动 — 功能开发中，敬请期待"
        action={<Button variant="secondary" onClick={() => navigate('/')}>浏览饰品</Button>}
      />
    </div>
  )
}
