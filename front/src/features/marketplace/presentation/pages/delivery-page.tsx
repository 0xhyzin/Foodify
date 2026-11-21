import { useCallback, useState } from "react";
import { Link } from "react-router";
import {
  Banknote,
  CheckCircle2,
  Clock3,
  MapPin,
  Phone,
  RefreshCw,
  Store,
  Truck,
} from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { formatMoney } from "../../domain/money";
import { ResourceState } from "../components/resource-state";
import { usePolledPage } from "../hooks/use-polled-page";
import {
  hasCourierRole,
  hasKitchenRole,
  hasManagerRole,
  nextCourierStage,
  orderLabels,
} from "../status-labels";

const courierFilters: [string, string][] = [
  ["", "الكل"],
  ["ready_for_pickup", "جاهزة للاستلام"],
  ["picked_up", "معي في الطريق"],
  ["delivered", "تم تسليمها"],
];

export function DeliveryPage() {
  const { marketplace: services } = useServices();
  const { user } = useSession();
  const [statusFilter, setStatusFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [busyOrderId, setBusyOrderId] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");

  const allowed = hasCourierRole(user?.roles);
  const queryKey = `${user?.id ?? ""}:${statusFilter}:${offset}`;

  const orders = usePolledPage(
    allowed,
    queryKey,
    useCallback(
      (signal: AbortSignal) =>
        services.delivery.listMyOrders(
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
        <p>بوابة التوصيل متاحة لمناديب التوصيل فقط.</p>
        {hasManagerRole(user?.roles) ? (
          <Link className="button button-primary" to="/operations">
            الانتقال إلى بوابة المدير
          </Link>
        ) : hasKitchenRole(user?.roles) ? (
          <Link className="button button-primary" to="/kitchen">
            الانتقال إلى بوابة تحضير الطلبات
          </Link>
        ) : (
          <Link className="button button-primary" to="/">
            العودة إلى المتجر
          </Link>
        )}
      </div>
    );
  }

  async function advanceDelivery(
    orderId: string,
    target: "PICKED_UP" | "DELIVERED",
  ) {
    if (busyOrderId) return;
    setBusyOrderId(orderId);
    setActionError("");
    try {
      await services.delivery.updateDeliveryStatus(orderId, target);
      orders.reload();
    } catch (cause) {
      setActionError(getErrorMessage(cause));
    } finally {
      setBusyOrderId(null);
    }
  }

  return (
    <>
      <div className="mp-page-heading">
        <Truck aria-hidden="true" />
        <h1 tabIndex={-1}>بوابة المندوب — طلبات التوصيل</h1>
        <p>
          تفاصيل الاستلام من المطعم، عنوان العميل الكامل بالتفصيل، وحالة التحصيل لكل طلب مسند إليك.
        </p>
      </div>

      <div className="mp-manager-controls">
        <div
          className="mp-filter-pills"
          role="group"
          aria-label="تصفية طلبات المندوب"
        >
          {courierFilters.map(([code, label]) => (
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
          تحديث الطلبات
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
        <div className="mp-courier-grid">
          {orders.data.items.map((order) => {
            const addr = order.deliveryAddressDetails;
            const nextAction = nextCourierStage(order.status);
            const isCod = order.paymentStatus === "due_on_delivery";
            const isBusy = busyOrderId === order.id;

            return (
              <article key={order.id} className="mp-courier-card">
                <div className="mp-section-title">
                  <div>
                    <h2>
                      طلب #<bdi>{order.id.slice(0, 8)}</bdi>
                    </h2>
                    <small className="mp-muted">
                      {new Date(order.createdAt).toLocaleString("ar-EG")}
                    </small>
                  </div>
                  <span className={`mp-status is-${order.status}`}>
                    {orderLabels[order.status] ?? order.status}
                  </span>
                </div>

                {order.status === "ready_for_pickup" ? (
                  <p className="mp-ready-callout">
                    <CheckCircle2 aria-hidden="true" size={17} />
                    الطلب جاهز للاستلام من المطعم الآن.
                  </p>
                ) : order.status === "accepted" || order.status === "preparing" ? (
                  <p className="mp-preparing-callout">
                    <Clock3 aria-hidden="true" size={17} />
                    المطبخ لا يزال يحضّر الطلب — سيصلك إشعار فور الجاهزية.
                  </p>
                ) : null}

                <div className="mp-courier-route">
                  <div className="mp-route-box">
                    <h3>
                      <Store aria-hidden="true" size={16} />
                      الاستلام من المطعم
                    </h3>
                    <strong>{order.restaurantName ?? "المطعم"}</strong>
                    <p>
                      {order.restaurantAddress ||
                        "راجع عنوان الفرع من بيانات المطعم"}
                    </p>
                  </div>

                  <div className="mp-route-box is-dropoff">
                    <div className="mp-route-box-head">
                      <h3>
                        <MapPin aria-hidden="true" size={16} />
                        عنوان توصيل العميل
                      </h3>
                      <a
                        className="mp-phone-btn"
                        href={`tel:${addr.phone}`}
                        dir="ltr"
                      >
                        <Phone aria-hidden="true" size={15} />
                        <bdi>{addr.phone}</bdi>
                      </a>
                    </div>
                    <strong>{addr.recipientName}</strong>
                    <dl className="mp-address-grid">
                      <div>
                        <dt>المدينة</dt>
                        <dd>{addr.city}</dd>
                      </div>
                      <div>
                        <dt>المنطقة</dt>
                        <dd>{addr.area}</dd>
                      </div>
                      <div>
                        <dt>الشارع</dt>
                        <dd>{addr.street}</dd>
                      </div>
                      <div>
                        <dt>العمارة</dt>
                        <dd>{addr.building}</dd>
                      </div>
                      {addr.floor ? (
                        <div>
                          <dt>الدور</dt>
                          <dd>{addr.floor}</dd>
                        </div>
                      ) : null}
                      {addr.apartment ? (
                        <div>
                          <dt>الشقة</dt>
                          <dd>{addr.apartment}</dd>
                        </div>
                      ) : null}
                    </dl>
                    {addr.deliveryNotes ? (
                      <p className="mp-delivery-notes">
                        ملاحظات العميل: {addr.deliveryNotes}
                      </p>
                    ) : null}
                  </div>
                </div>

                <div className={isCod ? "mp-cod-callout is-cod" : "mp-cod-callout"}>
                  <Banknote aria-hidden="true" size={18} />
                  {isCod ? (
                    <span>
                      تحصيل كاش عند التسليم:{" "}
                      <strong>{formatMoney(order.total)}</strong>
                    </span>
                  ) : (
                    <span>مدفوع مسبقًا — بدون تحصيل كاش</span>
                  )}
                </div>

                <details className="mp-courier-items">
                  <summary>
                    مراجعة الأصناف ({order.items.length.toLocaleString("ar-EG")})
                  </summary>
                  <ul>
                    {order.items.map((line, idx) => (
                      <li key={line.productId + idx}>
                        {line.quantity} × {line.name}
                      </li>
                    ))}
                  </ul>
                </details>

                {nextAction === "PICKED_UP" ? (
                  <Button
                    loading={isBusy}
                    disabled={Boolean(busyOrderId)}
                    onClick={() => void advanceDelivery(order.id, "PICKED_UP")}
                  >
                    تأكيد استلام الطلب من المطعم
                  </Button>
                ) : nextAction === "DELIVERED" ? (
                  <Button
                    loading={isBusy}
                    disabled={Boolean(busyOrderId)}
                    onClick={() => void advanceDelivery(order.id, "DELIVERED")}
                  >
                    {isCod
                      ? "تأكيد التسليم وتحصيل الكاش"
                      : "تأكيد التسليم للعميل"}
                  </Button>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="mp-resource">
          <h2>مفيش طلبات توصيل مسندة إليك حاليًا</h2>
          <p>هيوصلك إشعار فوري أول ما المدير يعيّن لك طلب.</p>
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
