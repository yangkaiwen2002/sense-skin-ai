import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import Navbar from "./components/Navbar";
import WorkspaceBanner from "./components/WorkspaceBanner";
import { lazy, Suspense, useEffect } from "react";
const Library = lazy(() => import("./pages/Library"));
const System = lazy(() => import("./pages/System"));
const News = lazy(() => import("./pages/News"));
const Home = lazy(() => import("./pages/Home"));
const ItemDetail = lazy(() => import("./pages/ItemDetail"));
const Compare = lazy(() => import("./pages/Compare"));
const RentVsBuy = lazy(() => import("./pages/RentVsBuy"));
const Watchlist = lazy(() => import("./pages/Watchlist"));
const Research = lazy(() => import("./pages/Research"));

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
        <WorkspaceBanner />
        <main id="main-content">
          <ErrorBoundary>
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
                <Route path="/library" element={<Library />} />
                <Route path="/system" element={<System />} />
                <Route path="/news" element={<News />} />
                <Route
                  path="*"
                  element={
                    <div className="page-shell state-panel">
                      <h1>页面未找到</h1>
                      <a className="action-primary" href="/">
                        返回市场
                      </a>
                    </div>
                  }
                />
                <Route path="/" element={<Home />} />
                <Route path="/research" element={<Research />} />
                <Route path="/research/:sessionId" element={<Research />} />
                <Route path="/item/:itemId" element={<ItemDetail />} />
                <Route path="/compare/:itemId" element={<Compare />} />
                <Route path="/rent-vs-buy" element={<RentVsBuy />} />
                <Route path="/watchlist" element={<Watchlist />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  );
}
