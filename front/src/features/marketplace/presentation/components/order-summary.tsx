import type { Order } from "../../domain/models";
import { formatMoney } from "../../domain/money";
export function OrderSummary({ order }: { order: Order }) {
  return (
    <section className="mp-invoice">
      <h2>تفاصيل الطلب</h2>
      <ul>
        {order.items.map((line, index) => (
          <li key={line.productId + index}>
            <span>
              {line.quantity} × {line.name}
            </span>
            <strong>{formatMoney(line.total)}</strong>
          </li>
        ))}
      </ul>
      <dl className="mp-totals">
        <div>
          <dt>قيمة المنتجات</dt>
          <dd>{formatMoney(order.subtotal)}</dd>
        </div>
        <div>
          <dt>التوصيل</dt>
          <dd>{formatMoney(order.deliveryFee)}</dd>
        </div>
        <div className="mp-total">
          <dt>الإجمالي</dt>
          <dd>{formatMoney(order.total)}</dd>
        </div>
      </dl>
      <p className="mp-muted">
        ملخص طلب إلكتروني.{" "}
        {order.paymentStatus === "paid"
          ? "تم تأكيد الدفع."
          : order.paymentStatus === "due_on_delivery"
            ? "الدفع عند الاستلام."
            : "حالة الدفع موضحة أعلى الطلب."}
      </p>
    </section>
  );
}
