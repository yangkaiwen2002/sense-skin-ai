import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CaretRight, ArrowsLeftRight } from '@phosphor-icons/react'
import { getItemCompare, getItemOverview } from '../services/api'
import SearchBar from '../components/SearchBar'
import PriceComparisonMetrics from '../components/PriceComparisonMetrics'
import PlatformComparisonTable from '../components/PlatformComparisonTable'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import Skeleton from '../components/ui/Skeleton'
import Button from '../components/ui/Button'

export default function Compare() {
  const { itemId } = useParams()
  const navigate = useNavigate()
  const [compare, setCompare] = useState(null), [item, setItem] = useState(null)
  const [loading, setLoading] = useState(true), [failed, setFailed] = useState(false), [reload, setReload] = useState(0)
  useEffect(() => {
    let ignore = false
    setLoading(true); setFailed(false); setCompare(null)
    Promise.all([getItemCompare(itemId), getItemOverview(itemId)]).then(([cmp, ov]) => {
      if (ignore) return
      setCompare(cmp); setItem(ov); setFailed(!cmp || !ov); setLoading(false)
    })
    return () => { ignore = true }
  }, [itemId, reload])
  const valid = compare?.platforms?.filter(p => Number.isFinite(p.current_price) && p.current_price > 0) || []
  return (
    <div className="page-shell">
      <div className="breadcrumb"><button onClick={() => navigate('/')}>饰品市场</button><CaretRight size={12} /><span>平台对比</span></div>
      <div className="page-heading"><div><span className="eyebrow">PRICE COMPARISON</span><h1>同一饰品，比较不同报价。</h1><p>同时核对平台、来源与采集时间，价差未包含手续费与提现限制。</p></div></div>
      <div className="max-w-xl mb-7"><SearchBar label="搜索对比饰品" placeholder="选择要对比的饰品…" onSelect={s => navigate(`/compare/${s.id}`)} /></div>
      {loading ? <div className="surface-card p-6 space-y-5" role="status" aria-label="正在加载平台报价"><Skeleton h={26} w="50%" /><Skeleton h={160} /></div>
        : failed ? <ErrorState message="平台报价暂时无法载入，请重试或选择其他饰品。" onRetry={() => setReload(n => n + 1)} />
        : <>
          <div className="page-heading"><div><h2 className="text-lg font-semibold">{item?.item_name}</h2><p>{[item?.weapon_type, item?.exterior, item?.rarity].filter(Boolean).join(' · ')}</p></div><Button onClick={() => navigate(`/item/${itemId}`)}>查看研究</Button></div>
          {!valid.length ? <EmptyState icon={ArrowsLeftRight} title="暂无可比较的报价" sub="该饰品尚无有效平台报价，请先刷新行情。" /> : <>
            <section className="surface-card p-5 sm:p-6 mb-5" aria-label="平台报价比较">
              <PriceComparisonMetrics platforms={compare.platforms} />
            </section>
            <section className="surface-card p-5 sm:p-6"><h2 className="text-sm font-semibold mb-3">指标与来源明细</h2><PlatformComparisonTable platforms={compare.platforms} /></section>
            <p className="field-help">报价明细保留全部来源；上方价差只比较同类型的新鲜报价，不代表可成交价格或购买建议。</p>
          </>}
        </>}
    </div>
  )
}
