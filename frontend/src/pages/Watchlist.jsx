import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Star, Trash, ArrowRight } from "@phosphor-icons/react";
import useWatchlist from "../hooks/useWatchlist";
import QuoteSource from "../components/QuoteSource";
import Skeleton from "../components/ui/Skeleton";
import SkinImage from "../components/SkinImage";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import { getItemOverview } from "../services/api";
import { formatCNY } from "../utils/formatters";
export default function Watchlist() {
  const navigate = useNavigate(),
    { ids, toggle, error } = useWatchlist();
  const [items, setItems] = useState([]),
    [loading, setLoading] = useState(false),
    [failed, setFailed] = useState(false),
    [reload, setReload] = useState(0);
  useEffect(() => {
    let ignore = false;
    setLoading(true);
    Promise.all(ids.map((id) => getItemOverview(id))).then((data) => {
      if (ignore) return;
      setItems(data.map((item, index) => item || { item_id: ids[index], unavailable: true }));
      setFailed(data.some((x) => !x));
      setLoading(false);
    });
    return () => {
      ignore = true;
    };
  }, [ids, reload]);
  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <span className="eyebrow">YOUR WATCHLIST</span>
          <h1>
            我的自选{" "}
            <span className="text-sm text-[var(--text-dim)]">{ids.length}</span>
          </h1>
          <p className="text-xs text-[var(--text-secondary)]">
            关注喜欢的饰品，随时回看行情与研究。收藏保存在当前浏览器。
          </p>
        </div>
        <Button onClick={() => navigate("/")}>浏览市场</Button>
      </div>
      {error && (
        <p role="alert" className="text-[var(--avoid)] mb-4">
          {error}
        </p>
      )}
      {failed && (
        <div role="alert" className="notice notice-error">
          部分饰品暂时无法载入。
          <button
            className="text-[var(--accent)] ml-2"
            onClick={() => setReload((x) => x + 1)}
          >
            重试
          </button>
        </div>
      )}
      {loading ? (
        <div className="watchlist-grid" role="status" aria-label="正在更新自选行情">{ids.map(id => <div key={id} className="surface-card p-4 space-y-4"><Skeleton h={180} /><Skeleton h={20} /><Skeleton h={14} w="70%" /></div>)}</div>
      ) : ids.length === 0 ? (
        <EmptyState
          icon={Star}
          title="把喜欢的饰品加入自选"
          sub="在饰品详情页点击「加入自选」，即可在这里集中查看。"
          action={
            <Button variant="primary" onClick={() => navigate("/")}>
              发现饰品
            </Button>
          }
        />
      ) : (
        <div className="watchlist-grid">
          {items.map((item) => (
            <article
              key={item.item_id}
              className="surface-card overflow-hidden watchlist-card"
            >
              {item.unavailable ? <div className="p-5"><h2 className="font-semibold mb-2">饰品 #{item.item_id}</h2><p className="muted-copy mb-4">当前无法载入，收藏仍为你保留。</p><div className="flex gap-2"><Button onClick={() => setReload(x => x + 1)}>重新加载</Button><Button variant="ghost" onClick={() => toggle(item.item_id)}>移出自选</Button></div></div> : <><button
                className="watchlist-art"
                onClick={() => navigate(`/item/${item.item_id}`)}
                aria-label={`查看${item.item_name}`}
              >
                <SkinImage iconUrl={item.icon_url} name={item.item_name} />
              </button>
              <div className="p-4">
                <h2 className="text-sm font-semibold mb-3">{item.item_name}</h2>
                <div className="flex justify-between items-center">
                  <span className="price-display text-lg">
                    {item.platforms?.[0]?.current_price != null
                      ? formatCNY(item.platforms[0].current_price)
                      : "暂无报价"}
                  </span>
                  <span className="text-xs text-[var(--text-dim)]">
                    {item.platforms?.[0]?.platform}
                  </span>
                </div>
                <QuoteSource quote={item.platforms?.[0]} />
                <div className="flex justify-between mt-4 border-t border-[var(--border-default)] pt-3">
                  <button
                    className="text-xs text-[var(--accent)] flex items-center gap-2 min-h-[40px]"
                    onClick={() => navigate(`/item/${item.item_id}`)}
                  >
                    查看研究
                    <ArrowRight />
                  </button>
                  <button
                    onClick={() => toggle(item.item_id)}
                    className="text-[var(--text-dim)] p-2 min-h-[40px] min-w-[40px]"
                    aria-label={`移除${item.item_name}`}
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </div></>}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
