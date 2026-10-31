import type { HttpClient } from "@/infrastructure/http/contracts";
import type { MarketplaceServices } from "../application/services";
import { HttpCatalogRepository } from "./http-catalog-repository";
import { HttpCartRepository } from "./http-cart-repository";
import { HttpOrderRepository } from "./http-order-repository";
import { HttpPaymentRepository } from "./http-payment-repository";
export function createHttpMarketplace(client: HttpClient): MarketplaceServices {
  return {
    catalog: new HttpCatalogRepository(client),
    carts: new HttpCartRepository(client),
    orders: new HttpOrderRepository(client),
    payments: new HttpPaymentRepository(client),
  };
}
