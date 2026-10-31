import type { HttpClient } from "@/infrastructure/http/contracts";
import type { PaymentRepository } from "../domain/payment-repository";
import type { PaymentMethodCode } from "../domain/models";
import type { Envelope, OrderDto } from "./dto";
import { orderFromDto } from "./mappers";
export class HttpPaymentRepository implements PaymentRepository {
  constructor(private readonly client: HttpClient) {}
  async methods(signal?: AbortSignal) {
    const result = await this.client.request<
      Envelope<{
        methods: {
          code: PaymentMethodCode;
          label: string;
          enabled: boolean;
          recipient?: string | null;
          recipient_name?: string | null;
        }[];
      }>
    >("/payments/methods", { authenticated: false, signal });
    return result.data.methods.map((m) => ({
      ...m,
      recipientName: m.recipient_name,
    }));
  }
  async start(id: string) {
    const result = await this.client.request<
      Envelope<{ checkout_url: string; expires_at: string }>
    >(`/orders/${encodeURIComponent(id)}/payment`, { method: "POST" });
    return { url: result.data.checkout_url, expiresAt: result.data.expires_at };
  }
  async claimTransfer(id: string, reference: string) {
    return orderFromDto(
      (
        await this.client.request<Envelope<{ order: OrderDto }>>(
          `/orders/${encodeURIComponent(id)}/transfer-claim`,
          { method: "POST", body: { reference } },
        )
      ).data.order,
    );
  }
  async reviewTransfer(
    id: string,
    decision: "approve" | "reject",
    reference: string,
    note: string,
  ) {
    return orderFromDto(
      (
        await this.client.request<Envelope<{ order: OrderDto }>>(
          `/operations/orders/${encodeURIComponent(id)}/transfer-review`,
          {
            method: "POST",
            body: { decision, verified_reference: reference, note },
          },
        )
      ).data.order,
    );
  }
}
