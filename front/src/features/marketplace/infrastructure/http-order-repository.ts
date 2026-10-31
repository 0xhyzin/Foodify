import type { HttpClient } from "@/infrastructure/http/contracts";
import type { OrderRepository } from "../domain/order-repository";
import type { CheckoutInput } from "../domain/models";
import type { Envelope, OrderDto, PaginationDto } from "./dto";
import { orderFromDto } from "./mappers";
export class HttpOrderRepository implements OrderRepository {
  constructor(private readonly client: HttpClient) {}
  async checkout(input: CheckoutInput, idempotencyKey: string) {
    const result = await this.client.request<Envelope<{ order: OrderDto }>>(
      "/checkout",
      {
        method: "POST",
        idempotencyKey,
        body: {
          restaurant_id: input.restaurantId,
          address_id: input.addressId,
          payment_method: input.method,
          expected_total: input.expectedTotal,
          cart_revision: input.cartRevision,
        },
      },
    );
    return orderFromDto(result.data.order);
  }
  private async page(path: string, offset = 0, signal?: AbortSignal) {
    const result = await this.client.request<
      Envelope<{ orders: OrderDto[]; pagination: PaginationDto }>
    >(`${path}${path.includes("?") ? "&" : "?"}limit=20&offset=${offset}`, {
      signal,
    });
    return {
      items: result.data.orders.map(orderFromDto),
      hasMore: result.data.pagination.has_more,
    };
  }
  list(offset = 0, signal?: AbortSignal) {
    return this.page("/orders", offset, signal);
  }
  restaurantOrders(id: string, offset = 0, signal?: AbortSignal) {
    return this.page(
      "/restaurant/orders?restaurant_id=" + encodeURIComponent(id),
      offset,
      signal,
    );
  }
  async get(id: string, signal?: AbortSignal) {
    return orderFromDto(
      (
        await this.client.request<Envelope<{ order: OrderDto }>>(
          "/orders/" + encodeURIComponent(id),
          { signal },
        )
      ).data.order,
    );
  }
  async updateStatus(id: string, status: string) {
    return orderFromDto(
      (
        await this.client.request<Envelope<{ order: OrderDto }>>(
          `/operations/orders/${encodeURIComponent(id)}/status`,
          { method: "PATCH", body: { status } },
        )
      ).data.order,
    );
  }
}
