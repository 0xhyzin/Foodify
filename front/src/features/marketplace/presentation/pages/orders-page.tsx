import { useCallback, useState } from "react";
import { Link } from "react-router";
import { Package } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "../components/resource-state";
import { formatMoney } from "../../domain/money";
import { orderLabels, paymentLabels } from "../status-labels";
export function OrdersPage() {
  const {
      marketplace: { orders },
    } = useServices(),
    { user } = useSession(),
    [offset, setOffset] = useState(0);
  const result = useResource(
    useCallback(
      (signal: AbortSignal) => orders.list(offset, signal),
      [orders, offset, user?.id],
    ),
  );
  return (
    <>
      <div className="mp-page-heading">
        <Package aria-hidden="true" />
        <h1 tabIndex={-1}>طلباتي</h1>
        <p>كل طلب لوحده، وكل تفاصيله في مكان واحد.</p>
      </div>
      {result.loading || result.error ? (
        <ResourceState
          loading={result.loading}
          error={result.error}
          retry={result.reload}
        />
      ) : result.data?.items.length ? (
        <div className="mp-order-list">
          {result.data.items.map((o) => (
            <Link className="mp-order-card" to={"/orders/" + o.id} key={o.id}>
              <div>
                <h2>طلب #{o.id.slice(0, 8)}</h2>
                <p>{new Date(o.createdAt).toLocaleString("ar-EG")}</p>
                <span className="mp-status">
                  {orderLabels[o.status] ?? o.status}
                </span>
                <p>{paymentLabels[o.paymentStatus] ?? o.paymentStatus}</p>
              </div>
              <div>
                <strong>{formatMoney(o.total)}</strong>
                <p>
                  {o.items.map((l) => `${l.quantity} × ${l.name}`).join("، ")}
                </p>
                <b>تفاصيل وتتبع الطلب</b>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="mp-resource">
          <h2>لسه مفيش طلبات</h2>
          <Link className="button button-primary" to="/">
            ابدأ بأول طلب
          </Link>
        </div>
      )}
      <div className="mp-pagination">
        {offset > 0 ? (
          <button
            onClick={() => setOffset((v) => Math.max(0, v - 20))}
            type="button"
          >
            السابق
          </button>
        ) : null}
        {result.data?.hasMore ? (
          <button onClick={() => setOffset((v) => v + 20)} type="button">
            التالي
          </button>
        ) : null}
      </div>
    </>
  );
}
