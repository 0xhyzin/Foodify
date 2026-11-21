import { useCallback, useState } from "react";
import { Link } from "react-router";
import { Bell, Check, CheckCheck } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "../components/resource-state";
import { notificationEventLabels } from "../status-labels";

export function NotificationsPage() {
  const {
    marketplace: { notifications },
  } = useServices();
  const { user } = useSession();
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [offset, setOffset] = useState(0);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);
  const [actionError, setActionError] = useState("");

  const result = useResource(
    useCallback(
      (signal: AbortSignal) =>
        notifications.list({ unreadOnly, offset, limit: 20 }, signal),
      [notifications, unreadOnly, offset, user?.id],
    ),
  );

  async function handleMarkRead(id: string) {
    if (busyId) return;
    setBusyId(id);
    setActionError("");
    try {
      await notifications.markRead(id);
      result.reload();
    } catch (cause) {
      setActionError(getErrorMessage(cause));
    } finally {
      setBusyId(null);
    }
  }

  async function handleMarkAllRead() {
    if (markingAll) return;
    setMarkingAll(true);
    setActionError("");
    try {
      await notifications.markAllRead();
      result.reload();
    } catch (cause) {
      setActionError(getErrorMessage(cause));
    } finally {
      setMarkingAll(false);
    }
  }

  const unreadCount = result.data?.unreadCount ?? 0;

  return (
    <>
      <div className="mp-page-heading">
        <Bell aria-hidden="true" />
        <h1 tabIndex={-1}>الإشعارات</h1>
        <p>تنبيهات حالة الطلبات، الدفع، التجهيز والتوصيل أولًا بأول.</p>
      </div>

      <div className="mp-notif-page-toolbar">
        <div className="mp-filter-pills" role="group" aria-label="تصفية الإشعارات">
          <button
            type="button"
            className={!unreadOnly ? "mp-pill-tab active" : "mp-pill-tab"}
            aria-pressed={!unreadOnly}
            onClick={() => {
              setUnreadOnly(false);
              setOffset(0);
            }}
          >
            الكل
          </button>
          <button
            type="button"
            className={unreadOnly ? "mp-pill-tab active" : "mp-pill-tab"}
            aria-pressed={unreadOnly}
            onClick={() => {
              setUnreadOnly(true);
              setOffset(0);
            }}
          >
            غير المقروءة ({unreadCount.toLocaleString("ar-EG")})
          </button>
        </div>

        {unreadCount > 0 ? (
          <Button
            variant="secondary"
            loading={markingAll}
            onClick={() => void handleMarkAllRead()}
          >
            <CheckCheck aria-hidden="true" size={16} />
            تحديد الكل كمقروء
          </Button>
        ) : null}
      </div>

      {actionError ? (
        <p className="mp-error" role="alert">
          {actionError}
        </p>
      ) : null}

      {result.loading || result.error ? (
        <ResourceState
          loading={result.loading}
          error={result.error}
          retry={result.reload}
        />
      ) : result.data?.items.length ? (
        <div className="mp-notif-page-list">
          {result.data.items.map((item) => {
            const unread = !item.readAt;
            return (
              <article
                key={item.id}
                className={
                  unread ? "mp-notif-card is-unread" : "mp-notif-card"
                }
              >
                <div className="mp-notif-card-head">
                  <span className="mp-status">
                    {notificationEventLabels[item.eventType] ?? item.eventType}
                  </span>
                  <time dateTime={item.createdAt}>
                    {new Date(item.createdAt).toLocaleString("ar-EG")}
                  </time>
                </div>
                <h2>{item.title}</h2>
                <p>{item.message}</p>
                <div className="mp-notif-card-actions">
                  <Link
                    className="button button-secondary"
                    to={`/orders/${item.orderId}`}
                  >
                    عرض الطلب #{item.orderId.slice(0, 8)}
                  </Link>
                  {unread ? (
                    <Button
                      variant="ghost"
                      loading={busyId === item.id}
                      onClick={() => void handleMarkRead(item.id)}
                    >
                      <Check aria-hidden="true" size={16} />
                      تحديد كمقروء
                    </Button>
                  ) : (
                    <span className="mp-muted">مقروء</span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="mp-resource">
          <h2>{unreadOnly ? "كل إشعاراتك مقروءة" : "مفيش إشعارات حاليًا"}</h2>
          <Link className="button button-primary" to="/orders">
            متابعة طلباتي
          </Link>
        </div>
      )}

      <div className="mp-pagination">
        {offset > 0 ? (
          <button
            type="button"
            onClick={() => setOffset((v) => Math.max(0, v - 20))}
          >
            السابق
          </button>
        ) : null}
        {result.data?.hasMore ? (
          <button type="button" onClick={() => setOffset((v) => v + 20)}>
            التالي
          </button>
        ) : null}
      </div>
    </>
  );
}
