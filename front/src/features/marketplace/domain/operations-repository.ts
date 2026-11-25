import type {
  CreateMenuItemInput,
  CreateRestaurantInput,
  CreateStaffInput,
  Merchant,
  Order,
  Page,
  PreparerOption,
  Product,
  StaffAccount,
  UpdateMenuItemInput,
  UpdateRestaurantInput,
  UpdateUserRolesInput,
} from "./models";

export interface OperationsRepository {
  listManagedRestaurants(signal?: AbortSignal): Promise<Merchant[]>;
  createRestaurant(input: CreateRestaurantInput): Promise<Merchant>;
  updateRestaurant(
    restaurantId: string,
    input: UpdateRestaurantInput,
  ): Promise<Merchant>;
  createMenuItem(
    restaurantId: string,
    input: CreateMenuItemInput,
  ): Promise<Product>;
  updateMenuItem(
    restaurantId: string,
    itemId: string,
    input: UpdateMenuItemInput,
  ): Promise<Product>;
  assignStaff(
    restaurantId: string,
    userId: string,
  ): Promise<{ restaurantId: string; userId: string }>;
  listPreparers(
    restaurantId?: string,
    signal?: AbortSignal,
  ): Promise<PreparerOption[]>;
  assignPreparer(
    orderId: string,
    preparerId: string,
    reassign?: boolean,
  ): Promise<Order>;
  listKitchenOrders(
    offset?: number,
    signal?: AbortSignal,
    status?: string,
  ): Promise<Page<Order>>;
  updateKitchenStatus(
    orderId: string,
    status: "preparing" | "ready_for_pickup",
    note?: string,
  ): Promise<Order>;
  listUsers(
    options?: {
      role?: string;
      search?: string;
      limit?: number;
      offset?: number;
    },
    signal?: AbortSignal,
  ): Promise<Page<StaffAccount>>;
  createStaff(input: CreateStaffInput): Promise<StaffAccount>;
  updateUserRoles(
    userId: string,
    input: UpdateUserRolesInput,
  ): Promise<StaffAccount>;
}
