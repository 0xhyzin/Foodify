import type { HttpClient } from "@/infrastructure/http/contracts";
import type { DeliveryRepository } from "../domain/delivery-repository";
import type {
  AssignDeliveryResultDto,
  CourierDto,
  Envelope,
  OrderDto,
  PaginationDto,
  ReassignDeliveryResultDto,
  UpdateDeliveryStatusResultDto,
} from "./dto";
import { courierFromDto, orderFromDto } from "./mappers";

export class HttpDeliveryRepository implements DeliveryRepository {
  constructor(private readonly client: HttpClient) {}

  async listCouriers(signal?: AbortSignal) {
    const result = await this.client.request<
      Envelope<{ couriers: CourierDto[] }>
    >("/delivery/couriers", { signal });
    return result.data.couriers.map(courierFromDto);
  }

  async assignCourier(orderId: string, deliveryPersonId: string) {
    await this.client.request<Envelope<AssignDeliveryResultDto>>(
      `/orders/${encodeURIComponent(orderId)}/delivery-assignment`,
      {
        method: "POST",
        body: { delivery_person_id: deliveryPersonId },
      },
    );
  }

  async reassignCourier(orderId: string, newDeliveryPersonId: string) {
    await this.client.request<Envelope<ReassignDeliveryResultDto>>(
      `/orders/${encodeURIComponent(orderId)}/delivery-assignment`,
      {
        method: "PATCH",
        body: { new_delivery_person_id: newDeliveryPersonId },
      },
    );
  }

  async listMyOrders(offset = 0, signal?: AbortSignal, status?: string) {
    const query = new URLSearchParams({
      limit: "20",
      offset: String(offset),
    });
    if (status) query.set("status", status);
    const result = await this.client.request<
      Envelope<{
        delivery_person_id: string;
        orders: OrderDto[];
        pagination: PaginationDto;
      }>
    >(`/delivery/my-orders?${query}`, { signal });
    return {
      items: result.data.orders.map(orderFromDto),
      hasMore: result.data.pagination.has_more,
    };
  }

  async updateDeliveryStatus(
    orderId: string,
    status: "PICKED_UP" | "DELIVERED",
    note?: string,
  ) {
    const result = await this.client.request<
      Envelope<UpdateDeliveryStatusResultDto>
    >(`/delivery/orders/${encodeURIComponent(orderId)}/status`, {
      method: "PATCH",
      body: note ? { status, note } : { status },
    });
    return orderFromDto(result.data.order);
  }
}
