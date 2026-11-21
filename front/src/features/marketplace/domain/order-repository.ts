import type { CheckoutInput, Order, Page } from "./models";
export interface OrderRepository {
  checkout(input: CheckoutInput, idempotencyKey: string): Promise<Order>;
  list(offset?: number, signal?: AbortSignal): Promise<Page<Order>>;
  get(id: string, signal?: AbortSignal): Promise<Order>;
  restaurantOrders(
    restaurantId: string,
    offset?: number,
    signal?: AbortSignal,
    status?: string,
  ): Promise<Page<Order>>;
  updateStatus(id: string, status: string, note?: string): Promise<Order>;
  cancel(id: string, note?: string): Promise<Order>;
}
