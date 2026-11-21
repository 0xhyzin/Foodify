import { Link, Outlet, useSearchParams } from "react-router";
import { BriefcaseBusiness, Heart, MapPin, ShoppingBag, UserRound } from "lucide-react";
import { useSession } from "@/app/providers/session-provider";
import { appConfig } from "@/app/config";
import { useMarketplace } from "./marketplace-provider";
import { NotificationBell } from "./components/notification-bell";
import { primaryPortalPath } from "./status-labels";
import "./marketplace.css";
const navigation = [
  ["", "الرئيسية"],
  ["restaurant", "مطاعم"],
  ["dessert", "حلويات وقهوة"],
  ["grocery", "بقالة"],
  ["offers", "العروض"],
  ["favorites", "المفضلة"],
];
export function MarketplaceLayout() {
  const [params] = useSearchParams();
  const section = params.get("section") ?? "";
  const { carts, issue } = useMarketplace(),
    { user } = useSession();
  const portalPath = primaryPortalPath(user?.roles);
  return (
    <div className="mp-frame" dir="rtl">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        انتقل للمحتوى
      </a>
      <header className="mp-header">
        <div className="mp-topbar">
          <Link to="/" className="logo" aria-label="Foodify الرئيسية">
            <span className="logo-mark">f</span>
            <span className="wordmark">foodify</span>
          </Link>
          <Link to="/account/addresses" className="mp-location">
            <MapPin aria-hidden="true" size={19} />
            <span>
              <small>نوصّل لحد عندك</small>اختار عنوان التوصيل
            </span>
          </Link>
          <div className="mp-header-actions">
            <Link to="/orders">طلباتي</Link>
            <NotificationBell portalContext="customer" />
            {portalPath ? (
              <Link
                className="mp-portal-entry"
                to={portalPath}
                aria-label="بوابة العمل"
              >
                <BriefcaseBusiness aria-hidden="true" size={17} />
                <span>بوابة العمل</span>
              </Link>
            ) : null}
            <Link to={user ? "/account" : "/login"}>
              <UserRound aria-hidden="true" size={19} />
              <span>{user ? user.name.split(" ")[0] : "دخول / حساب جديد"}</span>
            </Link>
            <Link className="mp-cart-link" to="/carts">
              <ShoppingBag aria-hidden="true" size={19} />
              سلالي <b>{carts.length.toLocaleString("ar-EG")}</b>
            </Link>
          </div>
        </div>
        <nav className="mp-nav" aria-label="الأقسام الرئيسية">
          {navigation.map(([key, name]) => (
            <Link
              className={section === key ? "active" : ""}
              key={key}
              to={key ? "/?section=" + key : "/"}
            >
              {key === "favorites" ? <Heart aria-hidden="true" size={16} /> : null}
              {name}
            </Link>
          ))}
        </nav>
      </header>
      {appConfig.isDemo ? (
        <div className="mp-demo-note">
          تجربة ديمو: المطاعم والأسعار للعرض، والدفع محاكاة بدون تحصيل أموال.
        </div>
      ) : null}
      {issue ? (
        <div className="mp-notice" role="alert">
          تعذّر تحديث السلال والمفضلة: {issue}
        </div>
      ) : null}
      <main id="main-content" className="mp-main" tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="mp-footer">
        <Link to="/" className="wordmark">
          foodify
        </Link>
        <span>كل اللي بتحبه، لحد بابك.</span>
        <Link to="/orders">طلباتي</Link>
        <Link to="/account/addresses">عناويني</Link>
      </footer>
    </div>
  );
}
