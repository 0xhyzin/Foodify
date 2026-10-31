import type { CatalogQuery, Category, Merchant, Page, Product } from "./models";
export interface CatalogRepository {
  list(query: CatalogQuery, signal?: AbortSignal): Promise<Page<Merchant>>;
  get(id: string, signal?: AbortSignal): Promise<Merchant>;
  menu(id: string, signal?: AbortSignal): Promise<Product[]>;
  categories(signal?: AbortSignal): Promise<Category[]>;
  favorites(signal?: AbortSignal): Promise<string[]>;
  setFavorite(id: string, favorite: boolean): Promise<string[]>;
}
