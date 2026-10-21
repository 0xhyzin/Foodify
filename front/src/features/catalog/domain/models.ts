export type FoodKind = 'burger' | 'pizza' | 'bowl' | 'wrap';
export type CatalogCategory = 'all' | FoodKind;

export interface Meal {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly price: number;
  readonly ingredients: readonly string[];
  readonly artwork: FoodKind;
}

export interface Restaurant {
  readonly id: string;
  readonly name: string;
  readonly category: FoodKind;
  readonly cuisine: string;
  readonly description: string;
  readonly rating: number;
  readonly deliveryMinutes: string;
  readonly deliveryFee: number;
  readonly artwork: FoodKind;
  readonly meals: readonly [Meal, Meal, Meal];
}
