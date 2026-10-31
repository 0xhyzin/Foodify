import { Plus } from "lucide-react";
import { useNavigate } from "react-router";
import { useSession } from "@/app/providers/session-provider";
import { useToast } from "@/app/providers/toast-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import type { Product } from "../../domain/models";
import { formatMoney } from "../../domain/money";
import { useMarketplace } from "../marketplace-provider";
import { FoodPhoto } from "./food-photo";
export function ProductCard({ product: p }: { product: Product }) {
  const { add, busy } = useMarketplace(),
    { user } = useSession(),
    navigate = useNavigate(),
    { showToast } = useToast();
  return (
    <article className="mp-product">
      <FoodPhoto kind={p.artwork} />
      <div>
        <h3>{p.name}</h3>
        <p>{p.description}</p>
        <div className="mp-product-bottom">
          <strong>{formatMoney(p.price)}</strong>
          <button
            type="button"
            disabled={busy || !p.available}
            aria-label={"إضافة " + p.name + " للسلة"}
            onClick={() => {
              if (!user) {
                navigate("/login");
                return;
              }
              void add(p.restaurantId, p.id)
                .then(() => showToast("اتضاف لسلة المتجر"))
                .catch((e) => showToast(getErrorMessage(e)));
            }}
          >
            <Plus aria-hidden="true" size={20} />
            {p.available ? "أضف" : "غير متاح"}
          </button>
        </div>
      </div>
    </article>
  );
}
