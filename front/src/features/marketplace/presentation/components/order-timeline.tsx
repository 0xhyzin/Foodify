import { Check, ChefHat, Package, Truck } from "lucide-react";
import type { Order } from "../../domain/models";
import { orderLabels, stages } from "../status-labels";
const icons = [Check, ChefHat, Package, Truck, Check];
export function OrderTimeline({ order }: { order: Order }) {
  const current = stages.indexOf(order.status);
  return (
    <ol className="mp-timeline" aria-label="مراحل توصيل الطلب">
      {stages.map((stage, index) => {
        const Icon = icons[index],
          event = order.events.find((e) => e.status === stage);
        return (
          <li
            key={stage}
            className={index <= current ? "complete" : ""}
            aria-current={index === current ? "step" : undefined}
          >
            <span>
              <Icon size={21} />
            </span>
            <div>
              <b>{orderLabels[stage]}</b>
              {event ? (
                <small>
                  {new Date(event.createdAt).toLocaleTimeString("ar-EG", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </small>
              ) : (
                <small>في انتظار التحديث</small>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
