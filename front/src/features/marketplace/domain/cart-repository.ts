import type { Cart } from "./models";
export interface CartRepository {
  list(signal?: AbortSignal): Promise<Cart[]>;
  get(restaurantId: string, signal?: AbortSignal): Promise<Cart>;
  add(restaurantId: string, productId: string, quantity: number): Promise<Cart>;
  update(restaurantId: string, lineId: string, quantity: number): Promise<Cart>;
  remove(restaurantId: string, lineId: string): Promise<Cart>;
  clear(restaurantId: string): Promise<Cart>;
}
