import type { CatalogRepository } from "../domain/catalog-repository";
import type { CartRepository } from "../domain/cart-repository";
import type { DeliveryRepository } from "../domain/delivery-repository";
import type { NotificationRepository } from "../domain/notification-repository";
import type { OperationsRepository } from "../domain/operations-repository";
import type { OrderRepository } from "../domain/order-repository";
import type { PaymentRepository } from "../domain/payment-repository";
export interface MarketplaceServices {
  catalog: CatalogRepository;
  carts: CartRepository;
  orders: OrderRepository;
  payments: PaymentRepository;
  delivery: DeliveryRepository;
  notifications: NotificationRepository;
  operations: OperationsRepository;
}
