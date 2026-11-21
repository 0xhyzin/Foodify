import { useCallback, useState } from "react";
import { Link } from "react-router";
import { RefreshCw } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "../components/resource-state";
import { OperationalOrder } from "../components/operational-order";
import { ManagerRestaurantsPanel } from "../components/manager-restaurants-panel";
import { hasCourierRole, hasKitchenRole, hasManagerRole } from "../status-labels";

const statusFilters: [string, string][] = [
  ["", "الكل"],
  ["pending", "طلبات جديدة"],
  ["accepted", "تم قبولها"],
  ["preparing", "قيد التحضير"],
  ["ready_for_pickup", "جاهزة للمندوب"],
  ["picked_up", "مع المندوب"],
  ["delivered", "تم التسليم"],
  ["rejected", "مرفوضة"],
  ["cancelled", "ملغاة"],
];

export function OperationsPage() {
  const { marketplace: services } = useServices();
  const { user } = useSession();
  const [tab, setTab] = useState<"orders" | "catalog">("orders");
  const [merchantId, setMerchantId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [offset, setOffset] = useState(0);

  const isManager = hasManagerRole(user?.roles);
  const isGlobalOperator = Boolean(
    user?.roles.some((r) => ["admin", "operations_manager"].includes(r)),
  );

  const restaurants = useResource(
    useCallback(
      (signal: AbortSignal) =>
        isManager
          ? services.operations.listManagedRestaurants(signal)
          : Promise.resolve([]),
      [services, isManager, user?.id],
    ),
  );

  const selected = restaurants.data?.some((r) => r.id === merchantId)
    ? merchantId
    : (restaurants.data?.[0]?.id ?? "");

  const orders = useResource(
    useCallback(
      (signal: AbortSignal) =>
        isManager && selected
          ? services.orders.restaurantOrders(
              selected,
              offset,
              signal,
              statusFilter || undefined,
            )
          : Promise.resolve({ items: [], hasMore: false }),
      [services, isManager, selected, offset, statusFilter, user?.id],
    ),
  );

  const couriers = useResource(
    useCallback(
      (signal: AbortSignal) =>
        isManager
          ? services.delivery.listCouriers(signal)
          : Promise.resolve([]),
      [services, isManager, user?.id],
    ),
  );

  const preparers = useResource(
    useCallback(
      (signal: AbortSignal) =>
        isManager && selected
          ? services.operations.listPreparers(selected, signal)
          : Promise.resolve([]),
      [services, isManager, selected, user?.id],
    ),
  );

  if (!isManager) {
    return (
      <div className="mp-resource">
        <h1>غير مصرح بالدخول</h1>
        <p>بوابة المدير متاحة لمديري المطاعم وفريق التشغيل فقط.</p>
        {hasKitchenRole(user?.roles) ? (
          <Link className="button button-primary" to="/kitchen">
            الانتقال إلى بوابة تحضير الطلبات
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

  function handleChanged() {
    orders.reload();
    couriers.reload();
    preparers.reload();
  }

  return (
    <>
      <div className="mp-page-heading">
        <h1 tabIndex={-1}>بوابة المدير — إدارة الطلبات والمطاعم</h1>
        <p>
          قبول ورفض الطلبات، تعيين المحضّر والمندوب، وإضافة وإدارة المطاعم والمنيو.
        </p>
      </div>

      <div className="mp-portal-tabs" role="tablist" aria-label="أقسام بوابة المدير">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "orders"}
          className={tab === "orders" ? "mp-tab-btn active" : "mp-tab-btn"}
          onClick={() => setTab("orders")}
        >
          إدارة الطلبات وتوجيه الفريق
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "catalog"}
          className={tab === "catalog" ? "mp-tab-btn active" : "mp-tab-btn"}
          onClick={() => setTab("catalog")}
        >
          إضافة وإدارة المطاعم والمنيو
        </button>
      </div>

      {restaurants.error ? (
        <ResourceState error={restaurants.error} retry={restaurants.reload} />
      ) : null}

      {tab === "catalog" ? (
        <ManagerRestaurantsPanel
          restaurants={restaurants.data ?? []}
          selectedId={selected}
          isGlobalOperator={isGlobalOperator}
          onSelectRestaurant={(id) => {
            setMerchantId(id);
            setOffset(0);
          }}
          onRestaurantsChanged={(newSelected) => {
            if (newSelected) setMerchantId(newSelected);
            restaurants.reload();
          }}
        />
      ) : (
        <>
          <div className="mp-manager-controls">
            <label className="mp-store-select">
              <span>المتجر</span>
              <select
                value={selected}
                onChange={(e) => {
                  setMerchantId(e.target.value);
                  setOffset(0);
                }}
              >
                {restaurants.data?.length ? (
                  restaurants.data.map((r) => (
                    <option value={r.id} key={r.id}>
                      {r.name}
                    </option>
                  ))
                ) : (
                  <option value="">لا توجد مطاعم متاحة</option>
                )}
              </select>
            </label>

            <button
              className="button button-secondary mp-refresh-btn"
              type="button"
              onClick={handleChanged}
            >
              <RefreshCw aria-hidden="true" size={16} />
              تحديث الطلبات
            </button>
          </div>

          <div
            className="mp-filter-pills"
            role="group"
            aria-label="تصفية الطلبات حسب الحالة"
          >
            {statusFilters.map(([code, label]) => (
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

          {!restaurants.loading && !restaurants.data?.length ? (
            <div className="mp-resource">
              <h2>لا توجد مطاعم مرتبطة بحسابك حاليًا</h2>
              {isGlobalOperator ? (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => setTab("catalog")}
                >
                  إضافة مطعم جديد
                </button>
              ) : null}
            </div>
          ) : orders.loading || orders.error ? (
            <ResourceState
              loading={orders.loading}
              error={orders.error}
              retry={handleChanged}
            />
          ) : orders.data?.items.length ? (
            <div className="mp-operations-grid">
              {orders.data.items.map((order) => (
                <OperationalOrder
                  key={order.id}
                  order={order}
                  couriers={couriers.data ?? []}
                  preparers={preparers.data ?? []}
                  onChanged={handleChanged}
                />
              ))}
            </div>
          ) : (
            <ResourceState error="مفيش طلبات مطابقة للتصفية دي حاليًا." />
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
      )}
    </>
  );
}
