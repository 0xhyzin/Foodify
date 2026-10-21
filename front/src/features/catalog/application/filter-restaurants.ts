import type { CatalogCategory, Restaurant } from '../domain/models';

function normalizeSearch(value: string): string {
  return value.toLowerCase().replace(/[أإآ]/g, 'ا').replace(/ى/g, 'ي').replace(/[\u064B-\u065F]/g, '').trim();
}

export function filterRestaurants(restaurants: readonly Restaurant[], query: string, category: CatalogCategory): readonly Restaurant[] {
  const search = normalizeSearch(query);
  return restaurants.filter(restaurant => {
    if (category !== 'all' && restaurant.category !== category) return false;
    const searchableText = [restaurant.name, restaurant.cuisine, ...restaurant.meals.map(meal => meal.name)].join(' ');
    return !search || normalizeSearch(searchableText).includes(search);
  });
}
