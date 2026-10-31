import type { Order, PaymentMethod } from "./models";
export interface PaymentRepository {
  methods(signal?: AbortSignal): Promise<PaymentMethod[]>;
  start(id: string): Promise<{ url: string; expiresAt: string }>;
  claimTransfer(id: string, reference: string): Promise<Order>;
  reviewTransfer(
    id: string,
    decision: "approve" | "reject",
    reference: string,
    note: string,
  ): Promise<Order>;
}
