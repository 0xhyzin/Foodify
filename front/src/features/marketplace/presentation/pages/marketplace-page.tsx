import { useCallback, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { Search, SlidersHorizontal } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import type { CatalogQuery, MerchantKind } from "../../domain/models";
import { useResource } from "../hooks/use-resource";
import { useMarketplace } from "../marketplace-provider";
import { FoodPhoto } from "../components/food-photo";
import { MerchantCard } from "../components/merchant-card";
import { ResourceState } from "../components/resource-state";
import { CatalogSampleNote } from "../components/catalog-sample-note";
export function MarketplacePage() {
  const {
      marketplace: { catalog },
    } = useServices(),
    { user } = useSession(),
    { favorites } = useMarketplace();
  const [params, setParams] = useSearchParams(),
    [search, setSearch] = useState(params.get("search") ?? "");
  const section = params.get("section") ?? "",
    category = params.get("category") ?? "",
    offset = Number(params.get("offset") ?? 0) || 0;
  const query: CatalogQuery = {
    search: params.get("search") || undefined,
    category: category || undefined,
    kind: ["restaurant", "dessert", "grocery"].includes(section)
      ? (section as MerchantKind)
      : undefined,
    sort: (params.get("sort") ?? "rating") as CatalogQuery["sort"],
    freeDelivery: section === "offers" || params.get("free") === "1",
    maxMinutes: params.get("fast") === "1" ? 30 : undefined,
    offset,
  };
  const queryKey = JSON.stringify(query),
    favoriteKey = favorites.join(",");
  const data = useResource(
    useCallback(
      async (signal: AbortSignal) => {
        if (section === "favorites") {
          if (!user) return { items: [], hasMore: false };
          const merchants = await Promise.all(
            favoriteKey
              .split(",")
              .filter(Boolean)
              .map((id) => catalog.get(id, signal)),
          );
          return { items: merchants, hasMore: false };
        }
        return catalog.list(JSON.parse(queryKey) as CatalogQuery, signal);
      },
      [catalog, queryKey, section, user?.id, favoriteKey],
    ),
  );
  const categories = useResource(
    useCallback((signal: AbortSignal) => catalog.categories(signal), [catalog]),
  );
  function set(name: string, value: string) {
    setParams((old) => {
      const next = new URLSearchParams(old);
      value ? next.set(name, value) : next.delete(name);
      if (name !== "offset") next.delete("offset");
      return next;
    });
  }
  const title =
    section === "grocery"
      ? "مقاضي البيت، من مكانك."
      : section === "dessert"
        ? "لحظة حلوة تستاهلها."
        : "جعان؟ اختار اللي على بالك.";
  return (
    <>
      <section className="mp-hero">
        <div>
          <span className="mp-hero-label">أكلك ومقاضيك في مكان واحد</span>
          <h1 tabIndex={-1}>{title}</h1>
          <p>
            مطاعمك المفضّلة، حاجة حلوة، أو احتياجات البيت.
            <br />
            اختار، اطلب، وإحنا نوصل لحد عندك.
          </p>
          <form
            className="mp-search"
            onSubmit={(e) => {
              e.preventDefault();
              set("search", search.trim().slice(0, 100));
            }}
          >
            <Search aria-hidden="true" size={21} />
            <label className="sr-only" htmlFor="market-search">
              ابحث عن مطعم أو منتج
            </label>
            <input
              id="market-search"
              type="search"
              maxLength={100}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="نفسك في إيه؟ اسم مطعم أو أكلة…"
            />
            <button type="submit">دور على أكلة</button>
          </form>
        </div>
        <div className="mp-hero-visual">
          <FoodPhoto
            kind={
              section === "grocery"
                ? "grocery"
                : section === "dessert"
                  ? "cake"
                  : "burger"
            }
          />
          <span className="mp-hero-stamp">اختيارات على مزاجك</span>
        </div>
      </section>
      <CatalogSampleNote />
      <section aria-labelledby="categories-heading" className="mp-categories">
        <div className="mp-section-title">
          <h2 id="categories-heading">نفسك في إيه النهارده؟</h2>
          <span>اختيارات أكتر لكل يوم</span>
        </div>
        <div className="mp-category-strip">
          <button
            className={!category ? "selected" : ""}
            onClick={() => set("category", "")}
            type="button"
          >
            <span className="mp-category-all">الكل</span>
            <b>كل الاختيارات</b>
          </button>
          {categories.data?.map((c) => (
            <button
              key={c.code}
              className={category === c.code ? "selected" : ""}
              onClick={() => set("category", category === c.code ? "" : c.code)}
              type="button"
              aria-pressed={category === c.code}
            >
              <FoodPhoto kind={c.artwork} />
              <b>{c.name}</b>
            </button>
          ))}
        </div>
        {categories.error ? <p role="alert">{categories.error}</p> : null}
      </section>
      <section aria-labelledby="merchants-heading">
        <div className="mp-section-title">
          <div>
            <h2 id="merchants-heading">
              {section === "favorites"
                ? "أماكنك المفضّلة"
                : section === "offers"
                  ? "توصيل مجاني عليك"
                  : section === "grocery"
                    ? "بقالة وسوبر ماركت"
                    : section === "dessert"
                      ? "حلويات وقهوة"
                      : "أماكن تحب تطلب منها"}
            </h2>
            <p>كل متجر له سلته وطلبه المستقل.</p>
          </div>
          <SlidersHorizontal aria-hidden="true" size={20} />
        </div>
        {section !== "favorites" ? (
          <div className="mp-filters">
            <label>
              الترتيب{" "}
              <select
                value={query.sort}
                onChange={(e) => set("sort", e.target.value)}
              >
                <option value="rating">الأعلى تقييمًا</option>
                <option value="fastest">الأسرع توصيلًا</option>
                <option value="delivery_fee">أقل رسوم توصيل</option>
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={query.freeDelivery}
                onChange={(e) => set("free", e.target.checked ? "1" : "")}
              />
              توصيل مجاني
            </label>
            <label>
              <input
                type="checkbox"
                checked={!!query.maxMinutes}
                onChange={(e) => set("fast", e.target.checked ? "1" : "")}
              />
              خلال ٣٠ دقيقة
            </label>
            {category || query.search ? (
              <button
                type="button"
                onClick={() => {
                  setParams(section ? { section } : {});
                  setSearch("");
                }}
              >
                مسح الفلاتر
              </button>
            ) : null}
          </div>
        ) : null}
        {section === "favorites" && !user ? (
          <div className="mp-resource">
            <p>سجّل دخولك عشان تحفظ أماكنك المفضّلة.</p>
            <Link className="button button-primary" to="/login">
              تسجيل الدخول
            </Link>
          </div>
        ) : data.loading || data.error ? (
          <ResourceState
            loading={data.loading}
            error={data.error}
            retry={data.reload}
          />
        ) : data.data?.items.length ? (
          <div className="mp-merchant-grid">
            {data.data.items.map((r) => (
              <MerchantCard key={r.id} merchant={r} />
            ))}
          </div>
        ) : (
          <ResourceState error="مفيش أماكن مطابقة. جرّب فئة تانية أو امسح الفلاتر." />
        )}
        <div className="mp-pagination">
          {offset > 0 ? (
            <button
              type="button"
              onClick={() => set("offset", String(Math.max(0, offset - 24)))}
            >
              السابق
            </button>
          ) : null}
          {data.data?.hasMore ? (
            <button
              type="button"
              onClick={() => set("offset", String(offset + 24))}
            >
              اختيارات أكتر
            </button>
          ) : null}
        </div>
      </section>
    </>
  );
}
