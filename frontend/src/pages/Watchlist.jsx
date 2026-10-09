import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Star, Trash, ArrowRight } from "@phosphor-icons/react";
import useWatchlist from "../hooks/useWatchlist";
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
      setItems(data.filter(Boolean));
      setFailed(data.some((x) => !x));
      setLoading(false);
    });
    return () => {
      ignore = true;
    };
  }, [ids, reload]);
  return (
    <div className="market-container py-8">
      <div className="flex justify-between items-start gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-semibold mb-2">
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
        <div role="alert" className="mb-4 text-sm">
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
        <p role="status" className="py-12 text-center text-[var(--text-dim)]">
          正在更新自选行情…
        </p>
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
              className="surface-card overflow-hidden"
            >
              <button
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
                <div className="flex justify-between mt-4 border-t border-[var(--border-default)] pt-3">
                  <button
                    className="text-xs text-[var(--accent)] flex items-center gap-2"
                    onClick={() => navigate(`/item/${item.item_id}`)}
                  >
                    查看研究
                    <ArrowRight />
                  </button>
                  <button
                    onClick={() => toggle(item.item_id)}
                    className="text-[var(--text-dim)] p-1"
                    aria-label={`移除${item.item_name}`}
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
