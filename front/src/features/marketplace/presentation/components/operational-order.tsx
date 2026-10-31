import { useState } from "react";
import type { Order } from "../../domain/models";
import { useServices } from "@/app/providers/services-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { Field } from "@/shared/ui/field";
import { orderLabels, paymentLabels, stages } from "../status-labels";
import { OrderSummary } from "./order-summary";
export function OperationalOrder({
  order,
  onChanged,
}: {
  order: Order;
  onChanged(): void;
}) {
  const { marketplace: services } = useServices(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [reference, setReference] = useState(""),
    [note, setNote] = useState(""),
    [confirmed, setConfirmed] = useState(false);
  const next = stages[stages.indexOf(order.status) + 1],
    canFulfill = ["paid", "due_on_delivery", "simulated"].includes(
      order.paymentStatus,
    );
  async function run(action: () => Promise<unknown>) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await action();
      onChanged();
    } catch (cause) {
      setError(getErrorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="mp-operational-order">
      <div className="mp-section-title">
        <h2>#{order.id.slice(0, 8)}</h2>
        <span className="mp-status">{orderLabels[order.status]}</span>
      </div>
      <p>
        {order.recipientName} · <bdi>{order.phone}</bdi>
      </p>
      <p>{order.deliveryAddress}</p>
      <p>{paymentLabels[order.paymentStatus]}</p>
      <details>
        <summary>عرض تفاصيل الطلب</summary>
        <OrderSummary order={order} />
      </details>
      {next && canFulfill ? (
        <Button
          loading={busy}
          onClick={() =>
            void run(() => services.orders.updateStatus(order.id, next))
          }
        >
          {next === "delivered" && order.paymentStatus === "due_on_delivery"
            ? "تأكيد التسليم وتحصيل الكاش"
            : orderLabels[next]}
        </Button>
      ) : null}
      {order.paymentStatus === "pending_review" ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(() =>
              services.payments.reviewTransfer(
                order.id,
                "approve",
                reference.trim(),
                note.trim(),
              ),
            );
          }}
        >
          <h3>مراجعة تحويل InstaPay</h3>
          <p>
            المرجع اللي أرسله العميل: <bdi>{order.claimedReference}</bdi>
          </p>
          <Field
            label="رقم العملية المؤكَّد من كشف الحساب"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            required
            minLength={6}
            maxLength={100}
            dir="ltr"
          />
          <Field
            label="ملاحظة المراجعة"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            required
            minLength={5}
            maxLength={250}
          />
          <label className="mp-review-check">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            راجعت الحساب وتأكدت من استلام نفس قيمة الطلب
          </label>
          <Button type="submit" loading={busy} disabled={!confirmed}>
            تأكيد استلام التحويل
          </Button>
          <Button
            variant="secondary"
            disabled={busy || note.trim().length < 5}
            onClick={() =>
              void run(() =>
                services.payments.reviewTransfer(
                  order.id,
                  "reject",
                  reference.trim() || order.claimedReference || "rejected",
                  note.trim(),
                ),
              )
            }
          >
            رفض التحويل مع الملاحظة
          </Button>
        </form>
      ) : null}
      {error ? (
        <p role="alert" className="mp-error">
          {error}
        </p>
      ) : null}
    </article>
  );
}
