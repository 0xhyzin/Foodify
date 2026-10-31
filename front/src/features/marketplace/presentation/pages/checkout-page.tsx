import { useCallback, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { ArrowRight, CreditCard, MapPin, ShieldCheck } from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { useMarketplace } from "../marketplace-provider";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "../components/resource-state";
import { formatMoney } from "../../domain/money";
import type { CheckoutInput, PaymentMethodCode } from "../../domain/models";
import { createCheckout } from "../../application/checkout/use-case";
import { createStartPayment } from "../../application/start-payment/use-case";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { useToast } from "@/app/providers/toast-provider";
export function CheckoutPage() {
  const { restaurantId = "" } = useParams(),
    services = useServices(),
    { user } = useSession(),
    { refresh } = useMarketplace(),
    navigate = useNavigate(),
    { showToast } = useToast();
  const [addressId, setAddressId] = useState(""),
    [method, setMethod] = useState<PaymentMethodCode | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const inFlight = useRef(false),
    retry = useRef<{ fingerprint: string; key: string } | null>(null);
  const result = useResource(
    useCallback(
      async (signal: AbortSignal) => {
        const [cart, merchant, addresses, methods] = await Promise.all([
          services.marketplace.carts.get(restaurantId, signal),
          services.marketplace.catalog.get(restaurantId, signal),
          services.account.listAddresses(),
          services.marketplace.payments.methods(signal),
        ]);
        return { cart, merchant, addresses, methods };
      },
      [services, restaurantId, user?.id],
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
  const { cart, merchant, addresses, methods } = result.data;
  const selectedAddress =
    addresses.find((a) => a.id === addressId) ??
    addresses.find((a) => a.isDefault) ??
    addresses[0];
  const selectedMethod =
    methods.find((m) => m.code === method && m.enabled) ??
    methods.find((m) => m.enabled);
  async function submit() {
    if (inFlight.current || !selectedAddress || !selectedMethod) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    const input: CheckoutInput = {
      restaurantId,
      addressId: selectedAddress.id,
      method: selectedMethod.code,
      expectedTotal: cart.total,
      cartRevision: cart.revision,
    };
    const fingerprint = JSON.stringify(input),
      storageKey = `foodify:checkout:v1:${user?.id}:${restaurantId}`;
    let key =
      retry.current?.fingerprint === fingerprint ? retry.current.key : "";
    if (!key) {
      try {
        const saved: unknown = JSON.parse(
          sessionStorage.getItem(storageKey) ?? "null",
        );
        if (
          saved &&
          typeof saved === "object" &&
          "fingerprint" in saved &&
          saved.fingerprint === fingerprint &&
          "key" in saved &&
          typeof saved.key === "string" &&
          /^[0-9a-f-]{36}$/i.test(saved.key)
        )
          key = saved.key;
      } catch {
        /* Memory remains available if browser storage is restricted. */
      }
    }
    if (!key) key = crypto.randomUUID();
    retry.current = { fingerprint, key };
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({ fingerprint, key }));
    } catch {
      /* Keep the same key in memory for retries. */
    }
    try {
      const order = await createCheckout(services.marketplace.orders)(
        input,
        key,
      );
      void refresh().catch(() => undefined);
      if (
        ["card", "vodafone_cash", "orange_cash"].includes(
          order.paymentMethod,
        ) &&
        order.paymentStatus !== "paid"
      ) {
        try {
          const payment = await createStartPayment(
            services.marketplace.payments,
          )(order.id);
          window.location.assign(payment.url);
        } catch (cause) {
          showToast(getErrorMessage(cause));
          navigate("/orders/" + order.id);
        }
      } else navigate("/orders/" + order.id);
    } catch (cause) {
      setError(getErrorMessage(cause));
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  if (!cart.items.length)
    return (
      <div className="mp-resource">
        <h1 tabIndex={-1}>السلة فاضية</h1>
        <Link
          className="button button-primary"
          to={"/restaurants/" + restaurantId}
        >
          اختار منتجاتك
        </Link>
      </div>
    );
  return (
    <>
      <Link className="mp-back" to={"/restaurants/" + restaurantId}>
        <ArrowRight aria-hidden="true" size={17} />
        الرجوع لسلة {merchant.name}
      </Link>
      <div className="mp-page-heading">
        <h1 tabIndex={-1}>كمّل طلبك</h1>
        <p>من {merchant.name}. طلب واحد من متجر واحد.</p>
      </div>
      <div className="mp-checkout-layout">
        <div>
          <section className="mp-checkout-section">
            <h2>
              <MapPin aria-hidden="true" size={21} />
              عنوان التوصيل
            </h2>
            {addresses.length ? (
              <fieldset>
                <legend className="sr-only">اختار عنوان التوصيل</legend>
                {addresses.map((a) => (
                  <label
                    className={`mp-choice ${a.id === selectedAddress?.id ? "chosen" : ""}`}
                    key={a.id}
                  >
                    <input
                      type="radio"
                      name="delivery-address"
                      value={a.id}
                      checked={a.id === selectedAddress?.id}
                      onChange={() => setAddressId(a.id)}
                    />
                    <span>
                      <b>
                        {a.label} · {a.recipientName}
                      </b>
                      <small>
                        {[a.city, a.area, a.street, a.building].join("، ")}
                      </small>
                      <small dir="ltr">{a.phoneNumber}</small>
                    </span>
                  </label>
                ))}
              </fieldset>
            ) : (
              <p>أضف عنوان التوصيل عشان تكمّل الطلب.</p>
            )}
            <Link to="/account/addresses/new">إضافة عنوان جديد</Link>
          </section>
          <section className="mp-checkout-section">
            <h2>
              <CreditCard aria-hidden="true" size={21} />
              هتدفع إزاي؟
            </h2>
            <fieldset>
              <legend className="sr-only">اختار وسيلة الدفع</legend>
              {methods.map((m) => (
                <label
                  className={`mp-choice ${m.code === selectedMethod?.code ? "chosen" : ""} ${!m.enabled ? "unavailable" : ""}`}
                  key={m.code}
                >
                  <input
                    type="radio"
                    name="payment-method"
                    disabled={!m.enabled || busy}
                    checked={m.code === selectedMethod?.code}
                    onChange={() => setMethod(m.code)}
                  />
                  <span>
                    <b>{m.label}</b>
                    <small>
                      {!m.enabled
                        ? "غير متاحة حاليًا"
                        : m.code === "instapay"
                          ? "تأكيد التحويل بيتم بعد المراجعة"
                          : m.code === "cash"
                            ? "ادفع عند وصول طلبك"
                            : m.code === "simulated"
                              ? "للتجربة فقط، مفيش أموال هتتخصم"
                              : "دفع آمن عن طريق Paymob"}
                    </small>
                  </span>
                </label>
              ))}
            </fieldset>
            {selectedMethod?.code === "instapay" ? (
              <p className="mp-notice">
                بيانات التحويل هتظهر بعد حفظ الطلب. ما تحوّلش قبل ما يظهر رقم
                الطلب.
              </p>
            ) : null}
          </section>
        </div>
        <aside className="mp-checkout-summary">
          <h2>طلبك من {merchant.name}</h2>
          <ul>
            {cart.items.map((l) => (
              <li key={l.id}>
                <span>
                  {l.quantity} × {l.name}
                </span>
                <strong>{formatMoney(l.total)}</strong>
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
              <dd>{formatMoney(cart.deliveryFee)}</dd>
            </div>
            <div className="mp-total">
              <dt>الإجمالي</dt>
              <dd>{formatMoney(cart.total)}</dd>
            </div>
          </dl>
          {error ? (
            <p role="alert" className="mp-error">
              {error}{" "}
              <button type="button" onClick={result.reload}>
                تحديث السلة
              </button>
            </p>
          ) : null}
          <Button
            className="mp-full"
            loading={busy}
            disabled={
              !selectedAddress ||
              !selectedMethod ||
              cart.items.some((l) => !l.available)
            }
            onClick={() => void submit()}
          >
            {selectedMethod?.code === "cash"
              ? "أكّد الطلب"
              : selectedMethod?.code === "instapay"
                ? "احفظ الطلب واعرض بيانات التحويل"
                : selectedMethod?.code === "simulated"
                  ? "أكّد الطلب التجريبي"
                  : "كمّل للدفع الآمن"}
          </Button>
          <p className="mp-secure">
            <ShieldCheck aria-hidden="true" size={16} />
            بيانات الدفع محمية. سلالك التانية محفوظة.
          </p>
        </aside>
      </div>
    </>
  );
}
