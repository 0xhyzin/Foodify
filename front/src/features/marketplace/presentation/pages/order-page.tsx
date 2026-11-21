import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useParams } from "react-router";
import {
  Ban,
  CheckCircle2,
  Clock3,
  CreditCard,
  MapPin,
  Phone,
  ShieldCheck,
  Truck,
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
    location = useLocation(),
    { marketplace: services } = useServices(),
    { order, error, refresh: refreshOrder } = useOrder(orderId),
    { refresh } = useMarketplace();
  const [reference, setReference] = useState(""),
    [busy, setBusy] = useState(false),
    [actionError, setActionError] = useState(""),
    [cancelOpen, setCancelOpen] = useState(false),
    [cancelNote, setCancelNote] = useState("");
  const [hostedCheckout, setHostedCheckout] = useState<{
    orderId: string;
    url: string;
    expiresAt: string;
  } | null>(null);
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
    ["pending", "failed"].includes(order.paymentStatus) &&
    !["rejected", "cancelled"].includes(order.status);
  const canCancel = ["awaiting_payment", "pending"].includes(order.status);
  const currentCheckout = hostedCheckout?.orderId === order.id &&
    Date.parse(hostedCheckout.expiresAt) > Date.now() ? hostedCheckout : null;
  const paymentSetupError = !currentCheckout && order.status === "awaiting_payment" &&
    typeof location.state?.paymentSetupError === "string"
    ? location.state.paymentSetupError : "";
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
          ) : order.status === "rejected" || order.status === "cancelled" ? (
            <Ban aria-hidden="true" size={32} />
          ) : (
            <CheckCircle2 aria-hidden="true" size={32} />
          )}
        </span>
        <div>
          <h1 tabIndex={-1}>{orderLabels[order.status] ?? order.status}</h1>
          <p>
            طلب #<bdi>{order.id.slice(0, 8)}</bdi>
            {order.restaurantName ? ` · ${order.restaurantName}` : ""} ·{" "}
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
            {order.transactionId || order.providerTransactionId ? (
              <dl className="mp-payment-meta">
                <div>
                  <dt>رقم الطلب</dt>
                  <dd>
                    <code dir="ltr">{order.id}</code>
                  </dd>
                </div>
                {order.transactionId ? (
                  <div>
                    <dt>معرّف عملية الدفع</dt>
                    <dd>
                      <code dir="ltr">{order.transactionId}</code>
                    </dd>
                  </div>
                ) : null}
                {order.providerTransactionId ? (
                  <div>
                    <dt>مرجع البوابة</dt>
                    <dd>
                      <code dir="ltr">{order.providerTransactionId}</code>
                    </dd>
                  </div>
                ) : null}
              </dl>
            ) : null}
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
                {currentCheckout ? (
                  <a className="button button-primary" href={currentCheckout.url} rel="noreferrer">
                    افتح Paymob وكمّل الدفع
                  </a>
                ) : <Button
                  loading={busy}
                  onClick={() =>
                    void run(async () => {
                      const result = await createStartPayment(
                        services.payments,
                      )(order.id);
                      setHostedCheckout({ orderId: order.id, ...result });
                      try {
                        window.location.assign(result.url);
                      } catch {
                        setActionError("بوابة الدفع جاهزة. افتحها من الرابط عشان تكمّل الدفع.");
                      }
                    })
                  }
                >
                  {order.paymentStatus === "failed"
                    ? "إعادة محاولة الدفع"
                    : "فتح بوابة الدفع"}
                </Button>}
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
            {actionError || paymentSetupError ? (
              <p className="mp-error" role="alert">
                {actionError || paymentSetupError}
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
            {order.deliveryAssignment ? (
              <div className="mp-courier-chip">
                <Truck aria-hidden="true" size={18} />
                <div>
                  <strong>
                    المندوب المسؤول: {order.deliveryAssignment.deliveryPersonName}
                  </strong>
                  <small>
                    تم التعيين:{" "}
                    {new Date(order.deliveryAssignment.assignedAt).toLocaleTimeString(
                      "ar-EG",
                      { hour: "2-digit", minute: "2-digit" },
                    )}
                  </small>
                </div>
              </div>
            ) : null}
            {canCancel ? (
              <div className="mp-cancel-box">
                {!cancelOpen ? (
                  <Button
                    variant="secondary"
                    disabled={busy}
                    onClick={() => setCancelOpen(true)}
                  >
                    إلغاء الطلب
                  </Button>
                ) : (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      void run(async () => {
                        await services.orders.cancel(
                          order.id,
                          cancelNote.trim() || undefined,
                        );
                        setCancelOpen(false);
                        setCancelNote("");
                      });
                    }}
                  >
                    <Field
                      label="سبب الإلغاء (اختياري)"
                      value={cancelNote}
                      onChange={(e) => setCancelNote(e.target.value)}
                      maxLength={250}
                      placeholder="مثال: غيرت رأيي أو عنوان خاطئ"
                    />
                    <div className="mp-inline-actions">
                      <Button type="submit" variant="danger" loading={busy}>
                        تأكيد إلغاء الطلب
                      </Button>
                      <Button
                        variant="secondary"
                        disabled={busy}
                        onClick={() => {
                          setCancelOpen(false);
                          setCancelNote("");
                        }}
                      >
                        تراجع
                      </Button>
                    </div>
                  </form>
                )}
              </div>
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
