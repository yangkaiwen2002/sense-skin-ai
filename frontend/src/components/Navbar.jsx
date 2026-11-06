import { Link, useLocation } from "react-router-dom";
import { ChartLineUp, Star, Calculator, Sparkle } from "@phosphor-icons/react";
const links = [
  { to: "/research", label: "AI 研究", icon: Sparkle },
  { to: "/", label: "饰品市场", icon: ChartLineUp },
  { to: "/rent-vs-buy", label: "租买计算", icon: Calculator },
  { to: "/watchlist", label: "我的自选", icon: Star },
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
              className={pathname === to || (to === '/research' && pathname.startsWith('/research/')) ? "active" : ""}
              aria-current={pathname === to || (to === '/research' && pathname.startsWith('/research/')) ? "page" : undefined}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <span className="nav-edition">CS2 MARKET INTELLIGENCE</span>
      </div>
    </header>
  );
}
