import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import {
  CheckCircle2,
  Clock3,
  CreditCard,
  MapPin,
  Phone,
  ShieldCheck,
} from "lucide-react";
import { useServices } from "@/app/providers/services-provider";
import { useMarketplace } from "../marketplace-provider";
import { useOrder } from "../hooks/use-order";
import { ResourceState } from "../components/resource-state";
import { OrderTimeline } from "../components/order-timeline";
import { OrderSummary } from "../components/order-summary";
import { createStartPayment } from "../../application/start-payment/use-case";
import { getErrorMessage } from "@/shared/domain/app-error";
import { orderLabels, paymentLabels } from "../status-labels";
import { formatMoney } from "../../domain/money";
import { Button } from "@/shared/ui/button";
import { Field } from "@/shared/ui/field";
export function OrderPage() {
  const { orderId = "" } = useParams(),
    { marketplace: services } = useServices(),
    { order, error, refresh: refreshOrder } = useOrder(orderId),
    { refresh } = useMarketplace();
  const [reference, setReference] = useState(""),
    [busy, setBusy] = useState(false),
    [actionError, setActionError] = useState("");
  const inFlight = useRef(false),
    paymentStatus = order?.paymentStatus;
  useEffect(() => {
    if (
      paymentStatus === "paid" ||
      paymentStatus === "simulated" ||
      paymentStatus === "due_on_delivery"
    )
      void refresh().catch(() => undefined);
  }, [paymentStatus, refresh]);
  if (!order)
    return (
      <ResourceState loading={!error} error={error} retry={refreshOrder} />
    );
  const canPay =
    ["card", "vodafone_cash", "orange_cash"].includes(order.paymentMethod) &&
    ["pending", "failed"].includes(order.paymentStatus);
  const run = async (action: () => Promise<unknown>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setActionError("");
    try {
      await action();
      refreshOrder();
    } catch (cause) {
      setActionError(getErrorMessage(cause));
      refreshOrder();
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  };
  return (
    <>
      <Link className="mp-back" to="/orders">
        كل طلباتي
      </Link>
      <section className="mp-confirmation">
        <span className="mp-confirmation-icon">
          {order.status === "awaiting_payment" ? (
            <Clock3 aria-hidden="true" size={32} />
          ) : (
            <CheckCircle2 aria-hidden="true" size={32} />
          )}
        </span>
        <div>
          <h1 tabIndex={-1}>{orderLabels[order.status] ?? order.status}</h1>
          <p>
            طلب #{order.id.slice(0, 8)} ·{" "}
            {new Date(order.createdAt).toLocaleString("ar-EG")}
          </p>
          <span className="mp-status">
            {paymentLabels[order.paymentStatus] ?? order.paymentStatus}
          </span>
        </div>
        <strong>{formatMoney(order.total)}</strong>
      </section>
      {order.simulated ? (
        <p className="mp-notice">
          ده طلب تجريبي. لم يتم تحصيل أموال، والتوصيل غير فعلي.
        </p>
      ) : null}
      {error ? (
        <p className="mp-notice" role="status">
          آخر تحديث: {error}
        </p>
      ) : null}
      <div className="mp-tracking-layout">
        <div>
          <section className="mp-checkout-section">
            <h2>
              <CreditCard aria-hidden="true" size={20} />
              حالة الدفع
            </h2>
            <p>{paymentLabels[order.paymentStatus] ?? order.paymentStatus}</p>
            {order.paymentStatus === "initializing" ? (
              <p className="mp-notice" role="status">
                بوابة الدفع بتتجهّز. استنى التحديث التلقائي قبل ما تفتحها، وما
                تعملش طلب جديد لنفس الدفع.
              </p>
            ) : order.paymentStatus === "initialization_unknown" ? (
              <p className="mp-notice" role="status">
                لسه مش قادرين نتأكد من تجهيز الدفع. ما تدفعش مرة تانية وما تعملش
                طلب بديل؛ تواصل مع الدعم برقم الطلب لمراجعة العملية.
              </p>
            ) : null}
            {canPay ? (
              <>
                <p>
                  هتنتقل لصفحة Paymob الآمنة لإتمام الدفع. تأكيد التحصيل هيظهر
                  هنا لما يوصلنا من البوابة.
                </p>
                <Button
                  loading={busy}
                  onClick={() =>
                    void run(async () => {
                      const result = await createStartPayment(
                        services.payments,
                      )(order.id);
                      window.location.assign(result.url);
                    })
                  }
                >
                  فتح بوابة الدفع
                </Button>
              </>
            ) : null}
            {order.paymentMethod === "instapay" &&
            order.paymentStatus !== "paid" ? (
              <>
                <p>
                  حوّل المبلغ بالضبط، واكتب رقم الطلب في وصف التحويل. التحويل لا
                  يؤكد الطلب قبل المراجعة.
                </p>
                {order.transferRecipient ? (
                  <div className="mp-transfer-details">
                    <b>{order.transferRecipientName}</b>
                    <code dir="ltr">{order.transferRecipient}</code>
                    <strong>{formatMoney(order.total)}</strong>
                  </div>
                ) : (
                  <p role="alert">
                    بيانات التحويل غير متاحة حاليًا. تواصل مع الدعم قبل التحويل.
                  </p>
                )}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void run(() =>
                      services.payments.claimTransfer(
                        order.id,
                        reference.trim(),
                      ),
                    );
                  }}
                >
                  <Field
                    label="رقم مرجع عملية التحويل"
                    value={reference}
                    onChange={(e) => setReference(e.target.value)}
                    required
                    minLength={6}
                    maxLength={100}
                    pattern="[A-Za-z0-9@._/+:-]+"
                    autoComplete="off"
                    dir="ltr"
                  />
                  <Button
                    type="submit"
                    loading={busy}
                    disabled={!reference.trim()}
                  >
                    إرسال للمراجعة
                  </Button>
                </form>
                {order.claimedReference ? (
                  <p>
                    المرجع المرسل: <bdi>{order.claimedReference}</bdi>
                  </p>
                ) : null}
              </>
            ) : null}
            {actionError ? (
              <p className="mp-error" role="alert">
                {actionError}
              </p>
            ) : null}
            <p className="mp-secure">
              <ShieldCheck aria-hidden="true" size={17} />
              تأكيد الدفع من السيرفر يحمي طلبك.
            </p>
          </section>
          <section className="mp-checkout-section">
            <h2>رحلة طلبك</h2>
            <p>الحالة بتتحدّث تلقائيًا. كل طلب ليه رحلة توصيل مستقلة.</p>
            <OrderTimeline order={order} />
            {order.status === "awaiting_payment" ? (
              <p className="mp-notice">التحضير هيبدأ بعد تأكيد الدفع.</p>
            ) : null}
          </section>
          <section className="mp-checkout-section">
            <h2>
              <MapPin aria-hidden="true" size={20} />
              عنوان التوصيل
            </h2>
            <b>{order.recipientName}</b>
            <p>{order.deliveryAddress}</p>
            <p className="mp-facts">
              <Phone aria-hidden="true" size={16} />
              <bdi>{order.phone}</bdi>
            </p>
          </section>
        </div>
        <aside>
          <OrderSummary order={order} />
          <Link className="button button-secondary mp-full" to="/carts">
            سلالي المحفوظة
          </Link>
          <button
            type="button"
            className="mp-print"
            onClick={() => window.print()}
          >
            طباعة ملخص الطلب
          </button>
        </aside>
      </div>
    </>
  );
}
