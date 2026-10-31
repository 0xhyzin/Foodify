import { useEffect, useState } from "react";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import type { Order } from "../../domain/models";
import { getErrorMessage } from "@/shared/domain/app-error";
export function useOrder(id: string) {
  const {
      marketplace: { orders },
    } = useServices(),
    { user } = useSession();
  const key = `${user?.id}:${id}`,
    [revision, setRevision] = useState(0);
  const [state, setState] = useState<{
    key: string;
    order?: Order;
    error?: string;
  }>();
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function poll() {
      if (controller.signal.aborted) return;
      let terminal = false;
      if (document.visibilityState !== "hidden")
        try {
          const order = await orders.get(id, controller.signal);
          if (controller.signal.aborted) return;
          setState({ key, order });
          terminal =
            order.status === "delivered" || order.paymentStatus === "refunded";
        } catch (error) {
          if (!controller.signal.aborted)
            setState((old) => ({
              key,
              order: old?.key === key ? old.order : undefined,
              error: getErrorMessage(error),
            }));
        }
      if (!terminal && !controller.signal.aborted)
        timer = setTimeout(() => void poll(), 5000);
    }
    void poll();
    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [orders, id, key, revision]);
  const current = state?.key === key ? state : undefined;
  return {
    order: current?.order,
    error: current?.error,
    refresh: () => setRevision((v) => v + 1),
  };
}
