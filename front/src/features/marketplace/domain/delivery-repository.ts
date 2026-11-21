import type { CourierOption, Order, Page } from "./models";

export interface DeliveryRepository {
  listCouriers(signal?: AbortSignal): Promise<CourierOption[]>;
  assignCourier(orderId: string, deliveryPersonId: string): Promise<void>;
  reassignCourier(orderId: string, newDeliveryPersonId: string): Promise<void>;
  listMyOrders(
    offset?: number,
    signal?: AbortSignal,
    status?: string,
  ): Promise<Page<Order>>;
  updateDeliveryStatus(
    orderId: string,
    status: "PICKED_UP" | "DELIVERED",
    note?: string,
  ): Promise<Order>;
}
