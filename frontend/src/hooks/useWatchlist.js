import { useEffect, useState } from "react";
import { readWatchlist, writeWatchlist } from "../utils/watchlist";
export default function useWatchlist() {
  const [ids, setIds] = useState(readWatchlist),
    [error, setError] = useState("");
  useEffect(() => {
    const sync = () => setIds(readWatchlist());
    window.addEventListener("storage", sync);
    window.addEventListener("watchlist-change", sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("watchlist-change", sync);
    };
  }, []);
  function toggle(id) {
    const current = readWatchlist(),
      next = current.includes(id)
        ? current.filter((x) => x !== id)
        : [...current, id];
    try {
      writeWatchlist(next);
      setIds(next);
      setError("");
    } catch {
      setError("浏览器无法保存收藏，请检查本地存储设置。");
    }
  }
  return { ids, toggle, error };
}
