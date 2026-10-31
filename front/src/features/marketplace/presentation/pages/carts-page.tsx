import { useCallback } from "react";
import { Link } from "react-router";
import { ShoppingBag } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useMarketplace } from "../marketplace-provider";
import { useResource } from "../hooks/use-resource";
import { CartPanel } from "../components/cart-panel";
import { ResourceState } from "../components/resource-state";
import { MerchantLogo } from "../components/merchant-logo";
export function CartsPage() {
  const { carts } = useMarketplace(),
    {
      marketplace: { catalog },
    } = useServices();
  const ids = carts
    .map((c) => c.restaurantId)
    .sort()
    .join(",");
  const result = useResource(
    useCallback(
      (signal: AbortSignal) =>
        Promise.all(
          ids
            .split(",")
            .filter(Boolean)
            .map((id) => catalog.get(id, signal)),
        ),
      [catalog, ids],
    ),
  );
  return (
    <>
      <div className="mp-page-heading">
        <ShoppingBag aria-hidden="true" />
        <h1 tabIndex={-1}>سلالي</h1>
        <p>كل مكان له سلته. كمّل طلب أي متجر وقت ما تحب.</p>
      </div>
      {result.loading || result.error ? (
        <ResourceState
          loading={result.loading}
          error={result.error}
          retry={result.reload}
        />
      ) : carts.length ? (
        <div className="mp-carts-grid">
          {carts.map((cart) => {
            const merchant = result.data?.find(
              (r) => r.id === cart.restaurantId,
            );
            return (
              <article key={cart.restaurantId}>
                <div className="mp-cart-merchant">
                  <MerchantLogo
                    logo={merchant?.logo ?? null}
                    name={merchant?.name ?? "المتجر"}
                  />
                  <Link to={"/restaurants/" + cart.restaurantId}>
                    {merchant?.name ?? "المتجر"} — كمّل تسوّق
                  </Link>
                </div>
                <CartPanel
                  cart={cart}
                  merchantId={cart.restaurantId}
                  name={merchant?.name ?? "المتجر"}
                />
              </article>
            );
          })}
        </div>
      ) : (
        <div className="mp-resource">
          <ShoppingBag aria-hidden="true" size={44} />
          <h2>اختياراتك الحلوة هتظهر هنا</h2>
          <p>افتح أي متجر وأضف منتجاتك. سلالك هتفضل محفوظة لكل متجر.</p>
          <Link className="button button-primary" to="/">
            اكتشف المتاجر
          </Link>
        </div>
      )}
    </>
  );
}
