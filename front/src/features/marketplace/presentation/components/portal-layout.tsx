import { Link, Outlet, useLocation } from "react-router";
import { ChefHat, ClipboardList, ShieldCheck, Truck, UserRound } from "lucide-react";
import { useSession } from "@/app/providers/session-provider";
import { appConfig } from "@/app/config";
import {
  hasAdminRole,
  hasCourierRole,
  hasKitchenRole,
  hasManagerRole,
} from "../status-labels";
import { NotificationBell, type PortalContext } from "./notification-bell";
import "../marketplace.css";

type PortalVariant = Exclude<PortalContext, "customer">;

const portalMeta: Record<
  PortalVariant,
  { badge: string; title: string; subtitle: string; Icon: typeof ClipboardList }
> = {
  admin: {
    badge: "بوابة الأدمن — إدارة المنصة",
    title: "لوحة تحكم الأدمن",
    subtitle: "إنشاء الطاقم، تعيين الأدوار والصلاحيات، وإدارة المطاعم.",
    Icon: ShieldCheck,
  },
  manager: {
    badge: "بوابة المدير",
    title: "إدارة المطعم والطلبات",
    subtitle: "قبول الطلبات، تعيين المحضّر والمندوب، وإدارة المطاعم والمنيو.",
    Icon: ClipboardList,
  },
  kitchen: {
    badge: "بوابة تحضير الطلبات",
    title: "شاشة المطبخ والتجهيز",
    subtitle: "استلام طلبات التحضير وتأكيد الجاهزية للمندوب.",
    Icon: ChefHat,
  },
  courier: {
    badge: "بوابة المندوب",
    title: "توصيل الطلبات",
    subtitle: "عرض الطلبات المسندة وعنوان العميل التفصيلي وتحديث حالة التوصيل.",
    Icon: Truck,
  },
};

export function PortalLayout({ variant }: { variant: PortalVariant }) {
  const { user } = useSession();
  const { pathname } = useLocation();
  const meta = portalMeta[variant];
  const Icon = meta.Icon;

  const showAdmin = hasAdminRole(user?.roles);
  const showManager = hasManagerRole(user?.roles);
  const showKitchen = hasKitchenRole(user?.roles);
  const showCourier = hasCourierRole(user?.roles);

  return (
    <div className={`mp-frame mp-portal-frame is-${variant}`} dir="rtl">
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

      <header className="mp-portal-header">
        <div className="mp-portal-topbar">
          <div className="mp-portal-brand">
            <span className="logo" aria-label="Foodify">
              <span className="logo-mark">f</span>
              <span className="wordmark">foodify</span>
            </span>
            <span className={`mp-portal-role-badge is-${variant}`}>
              <Icon aria-hidden="true" size={16} />
              {meta.badge}
            </span>
          </div>

          <nav className="mp-portal-nav" aria-label="بوابات العمل">
            {showAdmin ? (
              <Link
                to="/admin"
                className={pathname === "/admin" ? "active" : ""}
              >
                لوحة الأدمن
              </Link>
            ) : null}
            {showManager ? (
              <Link
                to="/operations"
                className={
                  pathname === "/operations" || pathname === "/manager"
                    ? "active"
                    : ""
                }
              >
                إدارة المدير
              </Link>
            ) : null}
            {showKitchen ? (
              <Link
                to="/kitchen"
                className={pathname === "/kitchen" ? "active" : ""}
              >
                تحضير الطلبات
              </Link>
            ) : null}
            {showCourier ? (
              <Link
                to="/delivery"
                className={pathname === "/delivery" ? "active" : ""}
              >
                التوصيل
              </Link>
            ) : null}
          </nav>

          <div className="mp-portal-actions">
            <NotificationBell portalContext={variant} />
            <Link to="/account" className="mp-portal-user">
              <UserRound aria-hidden="true" size={18} />
              <span>{user ? user.name.split(" ")[0] : "الحساب"}</span>
            </Link>
            <Link to="/" className="mp-portal-store-link">
              واجهة العميل
            </Link>
          </div>
        </div>
      </header>

      {appConfig.isDemo ? (
        <div className="mp-demo-note">
          وضع تشغيل تجريبي — التغييرات تطبق داخل بيئة العمل الحالية.
        </div>
      ) : null}

      <main id="main-content" className="mp-main mp-portal-main" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  );
}
