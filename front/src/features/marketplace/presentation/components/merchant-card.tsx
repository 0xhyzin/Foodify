import { Clock3, Heart, Star, Truck } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { useSession } from "@/app/providers/session-provider";
import { useToast } from "@/app/providers/toast-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import type { Merchant } from "../../domain/models";
import { formatMoney } from "../../domain/money";
import { useMarketplace } from "../marketplace-provider";
import { FoodPhoto } from "./food-photo";
import { MerchantLogo } from "./merchant-logo";
export function MerchantCard({ merchant: r }: { merchant: Merchant }) {
  const { favorites, favorite } = useMarketplace(),
    { user } = useSession(),
    navigate = useNavigate(),
    { showToast } = useToast();
  const saved = favorites.includes(r.id);
  return (
    <article className="mp-merchant-card">
      <Link
        to={"/restaurants/" + r.id}
        className="mp-cover-link"
        aria-label={"قائمة " + r.name}
      >
        <FoodPhoto kind={r.artwork} />
        {Number(r.deliveryFee) === 0 ? (
          <span className="mp-offer">توصيل مجاني</span>
        ) : null}
      </Link>
      <button
        type="button"
        className={`mp-favorite ${saved ? "is-saved" : ""}`}
        aria-label={(saved ? "إزالة من المفضلة: " : "إضافة للمفضلة: ") + r.name}
        aria-pressed={saved}
        onClick={() => {
          if (!user) {
            navigate("/login");
            return;
          }
          void favorite(r.id).catch((e) => showToast(getErrorMessage(e)));
        }}
      >
        <Heart aria-hidden="true" size={19} fill={saved ? "currentColor" : "none"} />
      </button>
      <div className="mp-merchant-body">
        <MerchantLogo logo={r.logo} name={r.name} />
        <div className="mp-merchant-title">
          <Link to={"/restaurants/" + r.id}>
            <h2>{r.name}</h2>
          </Link>
          <span>
            <Star aria-hidden="true" size={15} fill="currentColor" />
            {r.rating.toLocaleString("ar-EG")}{" "}
            <small>({r.reviews.toLocaleString("ar-EG")})</small>
          </span>
        </div>
        <p>{r.category}</p>
        <div className="mp-facts">
          <span>
            <Clock3 aria-hidden="true" size={15} />
            {r.minutes}–{r.minutes + 10} دقيقة
          </span>
          <span>
            <Truck aria-hidden="true" size={15} />
            {Number(r.deliveryFee) === 0
              ? "توصيل مجاني"
              : formatMoney(r.deliveryFee)}
          </span>
        </div>
      </div>
    </article>
  );
}
