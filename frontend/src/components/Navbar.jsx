import { Link, useLocation } from "react-router-dom";
import {
  ChartLineUp,
  Star,
  Calculator,
  Sparkle,
  Books,
  Newspaper,
  PlugsConnected,
} from "@phosphor-icons/react";
const links = [
  { to: "/", label: "饰品市场", icon: ChartLineUp },
  { to: "/research", label: "AI 研究", icon: Sparkle },
  { to: "/rent-vs-buy", label: "租买计算", icon: Calculator },
  { to: "/watchlist", label: "自选监控", icon: Star },
  { to: "/news", label: "事件中心", icon: Newspaper },
  { to: "/library", label: "研究库", icon: Books },
];
export default function Navbar() {
  const { pathname } = useLocation();
  return (
    <header className="site-header">
      <div className="site-nav">
        <Link to="/" className="brand">
          <span className="brand-symbol">S</span>
          <span>
            SenseSkin<small>饰品行情与研究</small>
          </span>
          <sup>AI</sup>
        </Link>
        <nav aria-label="主导航">
          {links.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={
                pathname === to ||
                (to === "/research" && pathname.startsWith("/research/"))
                  ? "active"
                  : ""
              }
              aria-current={
                pathname === to ||
                (to === "/research" && pathname.startsWith("/research/"))
                  ? "page"
                  : undefined
              }
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <Link to="/system" className="system-link" aria-label="连接与数据说明">
          <PlugsConnected size={20} />
          <span>连接与数据</span>
        </Link>
      </div>
    </header>
  );
}
