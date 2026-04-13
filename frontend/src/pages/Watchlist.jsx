import { useNavigate } from 'react-router-dom'

export default function Watchlist() {
  const navigate = useNavigate()
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <button onClick={() => navigate('/')} className="hover:text-slate-300 transition-colors">首页</button>
        <span>/</span>
        <span className="text-slate-300">我的关注</span>
      </div>
      <div className="text-center py-24">
        <div className="text-5xl mb-4">⭐</div>
        <h2 className="text-white text-xl font-semibold mb-2">关注列表</h2>
        <p className="text-slate-400 text-sm mb-6">收藏你关注的饰品，快速追踪价格变动</p>
        <p className="text-slate-600 text-xs">功能开发中，敬请期待</p>
        <button
          onClick={() => navigate('/')}
          className="mt-6 bg-slate-700 hover:bg-slate-600 text-white text-sm px-5 py-2.5 rounded-lg transition-colors"
        >
          浏览饰品
        </button>
      </div>
    </div>
  )
}
