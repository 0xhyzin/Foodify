import { useCallback, useState } from "react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "../components/resource-state";
import { OperationalOrder } from "../components/operational-order";
export function OperationsPage() {
  const { marketplace: services } = useServices(),
    { user } = useSession(),
    [merchantId, setMerchantId] = useState(""),
    [offset, setOffset] = useState(0);
  const catalog = useResource(
    useCallback(
      (signal: AbortSignal) => services.catalog.list({}, signal),
      [services],
    ),
  );
  const selected = merchantId || catalog.data?.items[0]?.id || "";
  const orders = useResource(
    useCallback(
      (signal: AbortSignal) =>
        selected
          ? services.orders.restaurantOrders(selected, offset, signal)
          : Promise.resolve({ items: [], hasMore: false }),
      [services, selected, offset, user?.id],
    ),
  );
  if (!user?.roles.some((r) => ["admin", "operations_manager"].includes(r)))
    return <ResourceState error="الصفحة دي متاحة لفريق إدارة الطلبات فقط." />;
  return (
    <>
      <div className="mp-page-heading">
        <h1 tabIndex={-1}>طلبات المتاجر</h1>
        <p>إدارة التحضير والتوصيل ومراجعة التحويلات.</p>
      </div>
      <label className="mp-store-select">
        المتجر{" "}
        <select
          value={selected}
          onChange={(e) => {
            setMerchantId(e.target.value);
            setOffset(0);
          }}
        >
          {catalog.data?.items.map((r) => (
            <option value={r.id} key={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </label>
      <ButtonRefresh onClick={orders.reload} />
      {catalog.error ? (
        <ResourceState error={catalog.error} retry={catalog.reload} />
      ) : null}
      {orders.loading || orders.error ? (
        <ResourceState
          loading={orders.loading}
          error={orders.error}
          retry={orders.reload}
        />
      ) : orders.data?.items.length ? (
        <div className="mp-operations-grid">
          {orders.data.items.map((order) => (
            <OperationalOrder
              key={order.id}
              order={order}
              onChanged={orders.reload}
            />
          ))}
        </div>
      ) : (
        <ResourceState error="مفيش طلبات للمتجر ده حاليًا." />
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
function ButtonRefresh({ onClick }: { onClick(): void }) {
  return (
    <button className="mp-print" type="button" onClick={onClick}>
      تحديث الطلبات
    </button>
  );
}
