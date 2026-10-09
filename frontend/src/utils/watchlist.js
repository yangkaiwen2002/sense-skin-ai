export const WATCHLIST_KEY = "senseskin.watchlist.v1";
export function parseWatchlist(raw) {
  try {
    const data = JSON.parse(raw);
    return Array.isArray(data)
      ? [...new Set(data.filter((x) => Number.isInteger(x) && x > 0))].slice(
          0,
          200,
        )
      : [];
  } catch {
    return [];
  }
}
export function readWatchlist() {
  try {
    return parseWatchlist(localStorage.getItem(WATCHLIST_KEY));
  } catch {
    return [];
  }
}
export function writeWatchlist(ids) {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(ids));
  window.dispatchEvent(new Event("watchlist-change"));
}
