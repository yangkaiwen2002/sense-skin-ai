import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import { lazy, Suspense, useEffect } from "react";
const Home = lazy(() => import("./pages/Home"));
const ItemDetail = lazy(() => import("./pages/ItemDetail"));
const Compare = lazy(() => import("./pages/Compare"));
const RentVsBuy = lazy(() => import("./pages/RentVsBuy"));
const Watchlist = lazy(() => import("./pages/Watchlist"));

function ScrollReset() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollReset />
      <div style={{ minHeight: "100vh", background: "var(--bg-page)" }}>
        <a href="#main-content" className="skip-link">
          跳到主要内容
        </a>
        <Navbar />
        <main id="main-content">
          <Suspense
            fallback={
              <div
                role="status"
                className="max-w-7xl mx-auto p-8 text-[var(--text-secondary)]"
              >
                正在加载研究工作区…
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/item/:itemId" element={<ItemDetail />} />
              <Route path="/compare/:itemId" element={<Compare />} />
              <Route path="/rent-vs-buy" element={<RentVsBuy />} />
              <Route path="/watchlist" element={<Watchlist />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  );
}
