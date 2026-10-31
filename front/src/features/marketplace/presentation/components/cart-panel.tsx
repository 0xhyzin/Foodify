import { useState } from "react";
import { Link } from "react-router";
import { Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import type { Cart } from "../../domain/models";
import { formatMoney } from "../../domain/money";
import { useMarketplace } from "../marketplace-provider";
import { useToast } from "@/app/providers/toast-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Dialog } from "@/shared/ui/dialog";
import { Button } from "@/shared/ui/button";
export function CartPanel({
  cart,
  merchantId,
  name,
}: {
  cart?: Cart;
  merchantId: string;
  name: string;
}) {
  const { busy, quantity, remove, clear } = useMarketplace(),
    { showToast } = useToast(),
    [confirm, setConfirm] = useState(false);
  const run = (action: Promise<unknown>) =>
    void action.catch((error) => showToast(getErrorMessage(error)));
  return (
    <section className="mp-cart-panel" aria-label={"سلة " + name}>
      <div className="mp-section-title">
        <h2>
          <ShoppingBag aria-hidden="true" size={20} />
          سلة {name}
        </h2>
        {cart?.items.length ? (
          <button
            type="button"
            disabled={busy}
            aria-label={"إفراغ سلة " + name}
            onClick={() => setConfirm(true)}
          >
            <Trash2 aria-hidden="true" size={18} />
          </button>
        ) : null}
      </div>
      <p className="mp-muted">سلة مستقلة. سلال المتاجر التانية محفوظة.</p>
      {cart?.items.length ? (
        <>
          <ul className="mp-cart-lines">
            {cart.items.map((line) => (
              <li key={line.id}>
                <div>
                  <strong>{line.name}</strong>
                  {!line.available ? (
                    <small className="mp-error">غير متاح حاليًا</small>
                  ) : null}
                  <span>{formatMoney(line.total)}</span>
                </div>
                <div className="mp-line-actions">
                  <div className="mp-quantity">
                    <button
                      type="button"
                      disabled={busy || line.quantity >= 99}
                      aria-label={"زيادة كمية " + line.name}
                      onClick={() =>
                        run(quantity(merchantId, line.id, line.quantity + 1))
                      }
                    >
                      <Plus aria-hidden="true" size={15} />
                    </button>
                    <span aria-label="الكمية">{line.quantity}</span>
                    <button
                      type="button"
                      disabled={busy || line.quantity <= 1}
                      aria-label={"تقليل كمية " + line.name}
                      onClick={() =>
                        run(quantity(merchantId, line.id, line.quantity - 1))
                      }
                    >
                      <Minus aria-hidden="true" size={15} />
                    </button>
                  </div>
                  <button
                    type="button"
                    disabled={busy}
                    className="mp-remove"
                    aria-label={"حذف " + line.name}
                    onClick={() => run(remove(merchantId, line.id))}
                  >
                    <Trash2 aria-hidden="true" size={16} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <dl className="mp-totals">
            <div>
              <dt>المنتجات</dt>
              <dd>{formatMoney(cart.subtotal)}</dd>
            </div>
            <div>
              <dt>التوصيل</dt>
              <dd>
                {Number(cart.deliveryFee) === 0
                  ? "مجاني"
                  : formatMoney(cart.deliveryFee)}
              </dd>
            </div>
            <div className="mp-total">
              <dt>الإجمالي</dt>
              <dd>{formatMoney(cart.total)}</dd>
            </div>
          </dl>
          {cart.items.every((l) => l.available) ? (
            <Link
              className="button button-primary mp-full"
              to={"/checkout/" + merchantId}
            >
              كمّل الطلب
            </Link>
          ) : (
            <p role="alert">احذف المنتجات غير المتاحة عشان تكمّل.</p>
          )}
        </>
      ) : (
        <div className="mp-empty-cart">
          <ShoppingBag aria-hidden="true" size={38} />
          <h3>سلتك لسه فاضية</h3>
          <p>أضف اللي على بالك من قائمة {name}.</p>
        </div>
      )}
      <Link className="mp-other-carts" to="/carts">
        عرض كل سلالي
      </Link>
      <Dialog
        open={confirm}
        onClose={() => setConfirm(false)}
        title={"إفراغ سلة " + name + "؟"}
      >
        <p>هتتمسح منتجات المتجر ده فقط.</p>
        <Button
          variant="danger"
          loading={busy}
          onClick={() => {
            void clear(merchantId)
              .then(() => setConfirm(false))
              .catch((e) => showToast(getErrorMessage(e)));
          }}
        >
          إفراغ السلة
        </Button>
        <Button variant="secondary" onClick={() => setConfirm(false)}>
          احتفظ بالسلة
        </Button>
      </Dialog>
    </section>
  );
}
