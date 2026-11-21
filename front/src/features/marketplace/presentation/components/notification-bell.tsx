import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { Bell, CheckCheck } from "lucide-react";
import { useSession } from "@/app/providers/session-provider";
import type { AppNotification } from "../../domain/models";
import { useNotifications } from "../hooks/use-notifications";
import { notificationEventLabels } from "../status-labels";

export type PortalContext = "customer" | "manager" | "kitchen" | "courier";

function destinationFor(
  portalContext: PortalContext,
  notification: AppNotification,
): string {
  switch (portalContext) {
    case "kitchen":
      return "/kitchen";
    case "courier":
      return "/delivery";
    case "manager":
      return "/operations";
    case "customer":
    default:
      return `/orders/${notification.orderId}`;
  }
}

export function NotificationBell({
  portalContext = "customer",
}: {
  portalContext?: PortalContext;
}) {
  const { user } = useSession();
  const { items, unreadCount, loading, error, markRead, markAllRead } =
    useNotifications(8);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  if (!user) return null;

  async function handleMarkAll() {
    if (busy || unreadCount === 0) return;
    setBusy(true);
    try {
      await markAllRead();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mp-notif-wrap" ref={wrapRef}>
      <button
        type="button"
        className="mp-notif-btn"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={
          unreadCount > 0
            ? `الإشعارات (${unreadCount} غير مقروء)`
            : "الإشعارات"
        }
        onClick={() => setOpen((v) => !v)}
      >
        <Bell aria-hidden="true" size={19} />
        {unreadCount > 0 ? (
          <span className="mp-notif-badge">
            {unreadCount > 99 ? "99+" : unreadCount.toLocaleString("ar-EG")}
          </span>
        ) : null}
      </button>

      {open ? (
        <div
          className="mp-notif-popover"
          role="dialog"
          aria-label="أحدث الإشعارات"
        >
          <div className="mp-notif-head">
            <strong>الإشعارات</strong>
            {unreadCount > 0 ? (
              <button
                type="button"
                className="mp-notif-markall"
                disabled={busy}
                onClick={() => void handleMarkAll()}
              >
                <CheckCheck aria-hidden="true" size={14} />
                تحديد الكل كمقروء
              </button>
            ) : null}
          </div>

          {error ? (
            <p className="mp-notif-empty" role="alert">
              {error}
            </p>
          ) : loading && !items.length ? (
            <p className="mp-notif-empty" role="status">
              جارٍ تحميل الإشعارات…
            </p>
          ) : items.length ? (
            <ul className="mp-notif-list">
              {items.map((item) => {
                const unread = !item.readAt;
                return (
                  <li
                    key={item.id}
                    className={
                      unread ? "mp-notif-item is-unread" : "mp-notif-item"
                    }
                  >
                    <Link
                      to={destinationFor(portalContext, item)}
                      onClick={() => {
                        if (unread) void markRead(item.id).catch(() => undefined);
                        setOpen(false);
                      }}
                    >
                      <div className="mp-notif-item-top">
                        <span className="mp-notif-kind">
                          {unread ? <i className="mp-notif-dot" aria-hidden="true" /> : null}
                          {notificationEventLabels[item.eventType] ?? item.title}
                        </span>
                        <time dateTime={item.createdAt}>
                          {new Date(item.createdAt).toLocaleTimeString("ar-EG", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </time>
                      </div>
                      <strong>{item.title}</strong>
                      <p>{item.message}</p>
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="mp-notif-empty">مفيش إشعارات جديدة حاليًا.</p>
          )}

          <div className="mp-notif-foot">
            <Link to="/notifications" onClick={() => setOpen(false)}>
              عرض جميع الإشعارات
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
