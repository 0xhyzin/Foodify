import { useCallback } from "react";
import { Link, useParams } from "react-router";
import { ArrowRight, Clock3, Star, Truck } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useMarketplace } from "../marketplace-provider";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "../components/resource-state";
import { FoodPhoto } from "../components/food-photo";
import { MerchantLogo } from "../components/merchant-logo";
import { ProductCard } from "../components/product-card";
import { CartPanel } from "../components/cart-panel";
import { CatalogSampleNote } from "../components/catalog-sample-note";
import { formatMoney } from "../../domain/money";
export function MerchantPage() {
  const { restaurantId = "" } = useParams(),
    {
      marketplace: { catalog },
    } = useServices(),
    { carts } = useMarketplace();
  const result = useResource(
    useCallback(
      async (signal: AbortSignal) => {
        const [merchant, products] = await Promise.all([
          catalog.get(restaurantId, signal),
          catalog.menu(restaurantId, signal),
        ]);
        return { merchant, products };
      },
      [catalog, restaurantId],
    ),
  );
  if (!result.data)
    return (
      <ResourceState
        loading={result.loading}
        error={result.error}
        retry={result.reload}
      />
    );
  const { merchant: r, products } = result.data;
  return (
    <>
      <Link className="mp-back" to="/">
        <ArrowRight aria-hidden="true" size={17} />
        كل الاختيارات
      </Link>
      <CatalogSampleNote />
      <section className="mp-merchant-hero">
        <FoodPhoto kind={r.artwork} />
        <div>
          <MerchantLogo logo={r.logo} name={r.name} />
          <h1 tabIndex={-1}>{r.name}</h1>
          <p>{r.description}</p>
          <div className="mp-facts">
            <span>
              <Star aria-hidden="true" size={16} />
              {r.rating}
            </span>
            <span>
              <Clock3 aria-hidden="true" size={16} />
              {r.minutes}–{r.minutes + 10} دقيقة
            </span>
            <span>
              <Truck aria-hidden="true" size={16} />
              {formatMoney(r.deliveryFee)}
            </span>
          </div>
        </div>
      </section>
      <div className="mp-menu-layout">
        <section>
          <div className="mp-section-title">
            <h2>
              {r.kind === "grocery" ? "منتجات المتجر" : "اختار اللي تحبه"}
            </h2>
            <span>{products.length} اختيارات</span>
          </div>
          <div className="mp-menu-grid">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
        <aside>
          <CartPanel
            cart={carts.find((c) => c.restaurantId === r.id)}
            merchantId={r.id}
            name={r.name}
          />
        </aside>
      </div>
    </>
  );
}
