import type { CatalogRepository } from "../domain/catalog-repository";
import type { CartRepository } from "../domain/cart-repository";
import type { OrderRepository } from "../domain/order-repository";
import type { PaymentRepository } from "../domain/payment-repository";
export interface MarketplaceServices {
  catalog: CatalogRepository;
  carts: CartRepository;
  orders: OrderRepository;
  payments: PaymentRepository;
}
