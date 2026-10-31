import type {
  HttpClient,
  RequestOptions,
} from "@/infrastructure/http/contracts";
import type { CartRepository } from "../domain/cart-repository";
import type { CartDto, Envelope, PaginationDto } from "./dto";
import { cartFromDto } from "./mappers";
export class HttpCartRepository implements CartRepository {
  constructor(private readonly client: HttpClient) {}
  async list(signal?: AbortSignal) {
    const carts: CartDto[] = [];
    for (let offset = 0; ; offset += 100) {
      const result = await this.client.request<Envelope<{carts: CartDto[]; pagination: PaginationDto}>>(`/carts?limit=100&offset=${offset}`, {signal});
      carts.push(...result.data.carts);
      if (!result.data.pagination.has_more) break;
    }
    return carts.map(cartFromDto);
  }
  private async request(id: string, suffix = "", options: RequestOptions = {}) {
    const result = await this.client.request<Envelope<{ cart: CartDto }>>(
      `/carts/${encodeURIComponent(id)}${suffix}`,
      options,
    );
    return cartFromDto(result.data.cart);
  }
  get(id: string, signal?: AbortSignal) {
    return this.request(id, "", { signal });
  }
  add(id: string, productId: string, quantity: number) {
    return this.request(id, "/items", {
      method: "POST",
      body: { menu_item_id: productId, quantity },
    });
  }
  update(id: string, lineId: string, quantity: number) {
    return this.request(id, `/items/${encodeURIComponent(lineId)}`, {
      method: "PATCH",
      body: { quantity },
    });
  }
  remove(id: string, lineId: string) {
    return this.request(id, `/items/${encodeURIComponent(lineId)}`, {
      method: "DELETE",
    });
  }
  clear(id: string) {
    return this.request(id, "", { method: "DELETE" });
  }
}
