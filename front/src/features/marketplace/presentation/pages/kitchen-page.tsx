import { useCallback, useState } from "react";
import { Link } from "react-router";
import { CheckCircle2, ChefHat, RefreshCw, Truck } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { ResourceState } from "../components/resource-state";
import { usePolledPage } from "../hooks/use-polled-page";
import {
  hasCourierRole,
  hasKitchenRole,
  hasManagerRole,
  nextKitchenStage,
  orderLabels,
} from "../status-labels";

const kitchenFilters: [string, string][] = [
  ["", "الكل"],
  ["accepted", "مقبولة — بانتظار البدء"],
  ["preparing", "جاري التحضير"],
  ["ready_for_pickup", "جاهزة للمندوب"],
];

export function KitchenPage() {
  const { marketplace: services } = useServices();
  const { user } = useSession();
  const [statusFilter, setStatusFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [busyOrderId, setBusyOrderId] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const allowed = hasKitchenRole(user?.roles);
  const queryKey = `${user?.id ?? ""}:${statusFilter}:${offset}`;

  const orders = usePolledPage(
    allowed,
    queryKey,
    useCallback(
      (signal: AbortSignal) =>
        services.operations.listKitchenOrders(
          offset,
          signal,
          statusFilter || undefined,
        ),
      [services, offset, statusFilter],
    ),
    10000,
  );

  if (!allowed) {
    return (
      <div className="mp-resource">
        <h1>غير مصرح بالدخول</h1>
        <p>بوابة تحضير الطلبات متاحة لمحضّري الطلبات ومديري المطاعم فقط.</p>
        {hasManagerRole(user?.roles) ? (
          <Link className="button button-primary" to="/operations">
            الانتقال إلى بوابة المدير
          </Link>
        ) : hasCourierRole(user?.roles) ? (
          <Link className="button button-primary" to="/delivery">
            الانتقال إلى بوابة المندوب
          </Link>
        ) : (
          <Link className="button button-primary" to="/">
            العودة إلى المتجر
          </Link>
        )}
      </div>
    );
  }

  async function advanceOrder(
    orderId: string,
    target: "preparing" | "ready_for_pickup",
  ) {
    if (busyOrderId) return;
    setBusyOrderId(orderId);
    setActionError("");
    try {
      await services.operations.updateKitchenStatus(orderId, target);
      orders.reload();
    } catch (cause) {
      setActionError(getErrorMessage(cause));
    } finally {
      setBusyOrderId(null);
    }
  }

  function toggleItem(key: string) {
    setCheckedItems((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <>
      <div className="mp-page-heading">
        <ChefHat aria-hidden="true" />
        <h1 tabIndex={-1}>بوابة تحضير الطلبات</h1>
        <p>
          ابدأ تحضير الطلبات المسندة للمطبخ وأكّد جاهزيتها فور الانتهاء ليتم إشعار المندوب بالاستلام.
        </p>
      </div>

      <div className="mp-manager-controls">
        <div
          className="mp-filter-pills"
          role="group"
          aria-label="تصفية تذاكر المطبخ"
        >
          {kitchenFilters.map(([code, label]) => (
            <button
              key={code || "all"}
              type="button"
              className={
                statusFilter === code ? "mp-pill-tab active" : "mp-pill-tab"
              }
              aria-pressed={statusFilter === code}
              onClick={() => {
                setStatusFilter(code);
                setOffset(0);
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="button button-secondary mp-refresh-btn"
          onClick={orders.reload}
        >
          <RefreshCw aria-hidden="true" size={16} />
          تحديث القائمة
        </button>
      </div>

      {actionError ? (
        <p className="mp-error" role="alert">
          {actionError}
        </p>
      ) : null}

      {orders.loading || (orders.error && !orders.data) ? (
        <ResourceState
          loading={orders.loading}
          error={orders.error}
          retry={orders.reload}
        />
      ) : orders.data?.items.length ? (
        <div className="mp-kitchen-grid">
          {orders.data.items.map((order) => {
            const nextStage = nextKitchenStage(order.status);
            const isBusy = busyOrderId === order.id;
            return (
              <article
                key={order.id}
                className={`mp-kitchen-card is-${order.status}`}
              >
                <div className="mp-section-title">
                  <div>
                    <h2>
                      تذكرة #<bdi>{order.id.slice(0, 8)}</bdi>
                    </h2>
                    <small className="mp-muted">
                      {order.restaurantName ?? "المطعم"} ·{" "}
                      {new Date(order.createdAt).toLocaleTimeString("ar-EG", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </small>
                  </div>
                  <span className={`mp-status is-${order.status}`}>
                    {orderLabels[order.status] ?? order.status}
                  </span>
                </div>

                <div className="mp-op-badges">
                  <span className="mp-op-chip">
                    <ChefHat aria-hidden="true" size={14} />
                    المحضّر: {order.assignedPreparer?.name ?? "قائمة المطبخ العامة"}
                  </span>
                  <span className="mp-op-chip">
                    <Truck aria-hidden="true" size={14} />
                    المندوب:{" "}
                    {order.deliveryAssignment?.deliveryPersonName ??
                      "لم يُعيَّن بعد"}
                  </span>
                </div>

                <ul className="mp-kitchen-checklist" aria-label="أصناف التذكرة">
                  {order.items.map((line, index) => {
                    const checkKey = `${order.id}:${line.productId}:${index}`;
                    const checked = Boolean(checkedItems[checkKey]);
                    return (
                      <li key={checkKey} className={checked ? "is-checked" : ""}>
                        <label>
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleItem(checkKey)}
                          />
                          <span>
                            <strong>{line.quantity} ×</strong> {line.name}
                          </span>
                        </label>
                      </li>
                    );
                  })}
                </ul>

                {nextStage === "preparing" ? (
                  <Button
                    loading={isBusy}
                    disabled={Boolean(busyOrderId)}
                    onClick={() => void advanceOrder(order.id, "preparing")}
                  >
                    بدء التحضير
                  </Button>
                ) : nextStage === "ready_for_pickup" ? (
                  <div className="mp-kitchen-ready-action">
                    <Button
                      loading={isBusy}
                      disabled={Boolean(busyOrderId)}
                      onClick={() =>
                        void advanceOrder(order.id, "ready_for_pickup")
                      }
                    >
                      تأكيد انتهاء التحضير — جاهز للاستلام
                    </Button>
                    <small className="mp-muted">
                      سيصل إشعار فوري للمندوب والعميل فور التأكيد.
                    </small>
                  </div>
                ) : order.status === "ready_for_pickup" ? (
                  <p className="mp-ready-callout">
                    <CheckCircle2 aria-hidden="true" size={17} />
                    الطلب جاهز — في انتظار استلام المندوب.
                  </p>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="mp-resource">
          <h2>مفيش طلبات مطبخ في التصفية دي حاليًا</h2>
          <p>هيوصلك إشعار فور ما المدير يقبل أو يوجّه طلب جديد للمطبخ.</p>
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
        {orders.data?.hasMore ? (
          <button type="button" onClick={() => setOffset((v) => v + 20)}>
            التالي
          </button>
        ) : null}
      </div>
    </>
  );
}
