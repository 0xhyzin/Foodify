import {
  Ban,
  Check,
  CheckCircle2,
  ChefHat,
  Clock3,
  PackageCheck,
  Truck,
} from "lucide-react";
import type { Order } from "../../domain/models";
import { orderLabels, stages } from "../status-labels";

const icons = [Clock3, CheckCircle2, ChefHat, PackageCheck, Truck, Check];

export function OrderTimeline({ order }: { order: Order }) {
  if (order.status === "rejected" || order.status === "cancelled") {
    const terminalEvent = [...order.events]
      .reverse()
      .find((e) => e.status === order.status);
    return (
      <div className="mp-terminal-banner" role="status">
        <Ban aria-hidden="true" size={22} />
        <div>
          <strong>{orderLabels[order.status] ?? order.status}</strong>
          {terminalEvent?.note ? <p>{terminalEvent.note}</p> : null}
          {terminalEvent ? (
            <small>
              {new Date(terminalEvent.createdAt).toLocaleString("ar-EG")}
            </small>
          ) : null}
        </div>
      </div>
    );
  }

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
