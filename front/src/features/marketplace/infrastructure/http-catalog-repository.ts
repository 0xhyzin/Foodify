import type { HttpClient } from "@/infrastructure/http/contracts";
import type { CatalogRepository } from "../domain/catalog-repository";
import type { CatalogQuery, Category } from "../domain/models";
import type { Envelope, MerchantDto, PaginationDto, ProductDto } from "./dto";
import { merchantFromDto, productFromDto } from "./mappers";
export class HttpCatalogRepository implements CatalogRepository {
  constructor(private readonly client: HttpClient) {}
  async list(query: CatalogQuery, signal?: AbortSignal) {
    const params = new URLSearchParams({
      limit: "24",
      offset: String(query.offset ?? 0),
      sort: query.sort ?? "rating",
    });
    if (query.kind) params.set("kind", query.kind);
    if (query.category) params.set("category", query.category);
    if (query.search) params.set("search", query.search);
    if (query.freeDelivery) params.set("free_delivery", "true");
    if (query.maxMinutes)
      params.set("max_delivery_minutes", String(query.maxMinutes));
    const result = await this.client.request<
      Envelope<{ restaurants: MerchantDto[]; pagination: PaginationDto }>
    >("/restaurants?" + params, { authenticated: false, signal });
    return {
      items: result.data.restaurants.map(merchantFromDto),
      hasMore: result.data.pagination.has_more,
    };
  }
  async get(id: string, signal?: AbortSignal) {
    const result = await this.client.request<
      Envelope<{ restaurant: MerchantDto }>
    >(`/restaurants/${encodeURIComponent(id)}`, {
      authenticated: false,
      signal,
    });
    return merchantFromDto(result.data.restaurant);
  }
  async menu(id: string, signal?: AbortSignal) {
    const items: ProductDto[] = [];
    for (let offset = 0; ; offset += 100) {
      const result = await this.client.request<
        Envelope<{ menu: ProductDto[]; pagination: PaginationDto }>
      >(
        `/restaurants/${encodeURIComponent(id)}/menu?limit=100&offset=${offset}`,
        { authenticated: false, signal },
      );
      items.push(...result.data.menu);
      if (!result.data.pagination.has_more || offset >= 900) break;
    }
    return items.map(productFromDto);
  }
  async categories(signal?: AbortSignal) {
    return (
      await this.client.request<Envelope<{ categories: Category[] }>>(
        "/catalog/categories",
        { authenticated: false, signal },
      )
    ).data.categories;
  }
  async favorites(signal?: AbortSignal) {
    return (
      await this.client.request<Envelope<{ restaurant_ids: string[] }>>(
        "/users/me/favorites",
        { signal },
      )
    ).data.restaurant_ids;
  }
  async setFavorite(id: string, favorite: boolean) {
    return (
      await this.client.request<Envelope<{ restaurant_ids: string[] }>>(
        `/users/me/favorites/${encodeURIComponent(id)}`,
        { method: "PUT", body: { favorite } },
      )
    ).data.restaurant_ids;
  }
}
