import { useEffect, useState } from "react";
import { ChefHat, Lock, Phone, Truck } from "lucide-react";
import type { CourierOption, Order, PreparerOption } from "../../domain/models";
import { useServices } from "@/app/providers/services-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { Field } from "@/shared/ui/field";
import {
  nextManagerStage,
  orderLabels,
  paymentLabels,
} from "../status-labels";
import { OrderSummary } from "./order-summary";

export function OperationalOrder({
  order,
  couriers,
  preparers,
  onChanged,
}: {
  order: Order;
  couriers: CourierOption[];
  preparers: PreparerOption[];
  onChanged(): void;
}) {
  const { marketplace: services } = useServices();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reference, setReference] = useState("");
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectNote, setRejectNote] = useState("");
  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelNote, setCancelNote] = useState("");

  const [selectedPreparer, setSelectedPreparer] = useState(
    order.assignedPreparer?.id ?? preparers[0]?.id ?? "",
  );
  const [selectedCourier, setSelectedCourier] = useState(
    order.deliveryAssignment?.deliveryPersonId ?? couriers[0]?.id ?? "",
  );

  useEffect(() => {
    setSelectedPreparer(order.assignedPreparer?.id ?? preparers[0]?.id ?? "");
  }, [order.assignedPreparer?.id, preparers]);

  useEffect(() => {
    setSelectedCourier(
      order.deliveryAssignment?.deliveryPersonId ?? couriers[0]?.id ?? "",
    );
  }, [order.deliveryAssignment?.deliveryPersonId, couriers]);

  const nextStage = nextManagerStage(order.status);
  const canFulfill = ["paid", "due_on_delivery", "simulated"].includes(
    order.paymentStatus,
  );
  const canAssign = ["accepted", "preparing", "ready_for_pickup"].includes(
    order.status,
  );
  const assignmentLocked =
    ["picked_up", "delivered"].includes(order.status) &&
    Boolean(order.deliveryAssignment);
  const canCancel = ["awaiting_payment", "pending"].includes(order.status);

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
        <h2>
          #{order.id.slice(0, 8)}
          {order.restaurantName ? ` · ${order.restaurantName}` : ""}
        </h2>
        <span className={`mp-status is-${order.status}`}>
          {orderLabels[order.status] ?? order.status}
        </span>
      </div>

      <p className="mp-op-customer">
        <span>{order.recipientName}</span>
        <span>·</span>
        <a href={`tel:${order.phone}`} dir="ltr">
          <Phone aria-hidden="true" size={14} />
          <bdi>{order.phone}</bdi>
        </a>
      </p>
      <p>{order.deliveryAddress}</p>
      <p>{paymentLabels[order.paymentStatus] ?? order.paymentStatus}</p>

      <div className="mp-op-badges">
        <span className="mp-op-chip">
          <ChefHat aria-hidden="true" size={14} />
          المحضّر: {order.assignedPreparer?.name ?? "غير معيّن"}
        </span>
        <span className="mp-op-chip">
          <Truck aria-hidden="true" size={14} />
          المندوب: {order.deliveryAssignment?.deliveryPersonName ?? "غير معيّن"}
        </span>
      </div>

      <details>
        <summary>عرض تفاصيل الطلب</summary>
        <OrderSummary order={order} />
      </details>

      {order.status === "pending" && canFulfill ? (
        <div className="mp-op-decision">
          <div className="mp-inline-actions">
            <Button
              loading={busy}
              onClick={() =>
                void run(() => services.orders.updateStatus(order.id, "accepted"))
              }
            >
              قبول الطلب
            </Button>
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => setRejectOpen((v) => !v)}
            >
              رفض الطلب
            </Button>
          </div>
          {rejectOpen ? (
            <form
              className="mp-inline-subform"
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  await services.orders.updateStatus(
                    order.id,
                    "rejected",
                    rejectNote.trim() || undefined,
                  );
                  setRejectOpen(false);
                  setRejectNote("");
                });
              }}
            >
              <Field
                label="سبب الرفض (اختياري)"
                value={rejectNote}
                onChange={(e) => setRejectNote(e.target.value)}
                maxLength={250}
                placeholder="مثال: صنف غير متاح حاليًا"
              />
              <Button type="submit" variant="danger" loading={busy}>
                تأكيد رفض الطلب
              </Button>
            </form>
          ) : null}
        </div>
      ) : null}

      {nextStage && canFulfill ? (
        <div className="mp-op-stage-action">
          <Button
            loading={busy}
            onClick={() =>
              void run(() => services.orders.updateStatus(order.id, nextStage))
            }
          >
            {nextStage === "preparing"
              ? "بدء التحضير"
              : "تأكيد انتهاء التحضير — جاهز للاستلام"}
          </Button>
        </div>
      ) : null}

      {canAssign ? (
        <div className="mp-assign-grid">
          <div className="mp-assign-row">
            <label>
              <span>تعيين محضّر الطلبات</span>
              <select
                value={selectedPreparer}
                onChange={(e) => setSelectedPreparer(e.target.value)}
                disabled={busy || !preparers.length}
              >
                {preparers.length ? (
                  preparers.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.activeOrderCount.toLocaleString("ar-EG")} نشط)
                    </option>
                  ))
                ) : (
                  <option value="">لا يوجد محضّرون متاحون</option>
                )}
              </select>
            </label>
            <Button
              variant="secondary"
              loading={busy}
              disabled={
                !selectedPreparer ||
                selectedPreparer === order.assignedPreparer?.id
              }
              onClick={() =>
                void run(() =>
                  services.operations.assignPreparer(
                    order.id,
                    selectedPreparer,
                    Boolean(order.assignedPreparer),
                  ),
                )
              }
            >
              {order.assignedPreparer ? "تغيير المحضّر" : "تعيين محضّر"}
            </Button>
          </div>

          <div className="mp-assign-row">
            <label>
              <span>تعيين مندوب التوصيل</span>
              <select
                value={selectedCourier}
                onChange={(e) => setSelectedCourier(e.target.value)}
                disabled={busy || !couriers.length}
              >
                {couriers.length ? (
                  couriers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.activeOrderCount.toLocaleString("ar-EG")} نشط)
                    </option>
                  ))
                ) : (
                  <option value="">لا يوجد مناديب متاحون</option>
                )}
              </select>
            </label>
            <Button
              variant="secondary"
              loading={busy}
              disabled={
                !selectedCourier ||
                selectedCourier === order.deliveryAssignment?.deliveryPersonId
              }
              onClick={() =>
                void run(() =>
                  order.deliveryAssignment
                    ? services.delivery.reassignCourier(order.id, selectedCourier)
                    : services.delivery.assignCourier(order.id, selectedCourier),
                )
              }
            >
              {order.deliveryAssignment ? "تغيير المندوب" : "تعيين مندوب"}
            </Button>
          </div>
        </div>
      ) : null}

      {assignmentLocked && order.deliveryAssignment ? (
        <p className="mp-locked-note">
          <Lock aria-hidden="true" size={14} />
          المندوب: {order.deliveryAssignment.deliveryPersonName} — التغيير مقفول بعد استلام الطلب.
        </p>
      ) : null}

      {canCancel ? (
        <div className="mp-cancel-box">
          {!cancelOpen ? (
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => setCancelOpen(true)}
            >
              إلغاء الطلب
            </Button>
          ) : (
            <form
              className="mp-inline-subform"
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
              />
              <div className="mp-inline-actions">
                <Button type="submit" variant="danger" loading={busy}>
                  تأكيد الإلغاء
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
