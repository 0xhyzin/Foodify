import type { HttpClient } from "@/infrastructure/http/contracts";
import type { OperationsRepository } from "../domain/operations-repository";
import type {
  CreateMenuItemInput,
  CreateRestaurantInput,
  CreateStaffInput,
  UpdateMenuItemInput,
  UpdateRestaurantInput,
  UpdateUserRolesInput,
} from "../domain/models";
import type {
  AdminUserDto,
  Envelope,
  MerchantDto,
  OrderDto,
  PaginationDto,
  PreparerDto,
  ProductDto,
} from "./dto";
import {
  merchantFromDto,
  orderFromDto,
  preparerFromDto,
  productFromDto,
  staffAccountFromDto,
} from "./mappers";

function compactBody(record: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(record).filter(([, value]) => value !== undefined),
  );
}

export class HttpOperationsRepository implements OperationsRepository {
  constructor(private readonly client: HttpClient) {}

  async listManagedRestaurants(signal?: AbortSignal) {
    const result = await this.client.request<
      Envelope<{ restaurants: MerchantDto[] }>
    >("/operations/restaurants", { signal });
    return result.data.restaurants.map(merchantFromDto);
  }

  async createRestaurant(input: CreateRestaurantInput) {
    const result = await this.client.request<
      Envelope<{ restaurant: MerchantDto }>
    >("/operations/restaurants", {
      method: "POST",
      body: compactBody({
        name: input.name,
        category: input.category,
        kind: input.kind,
        address: input.address,
        delivery_fee: input.deliveryFee,
        delivery_minutes: input.deliveryMinutes,
        description: input.description,
        artwork: input.artwork,
        is_active: input.isActive,
      }),
    });
    return merchantFromDto(result.data.restaurant);
  }

  async updateRestaurant(restaurantId: string, input: UpdateRestaurantInput) {
    const result = await this.client.request<
      Envelope<{ restaurant: MerchantDto }>
    >(`/operations/restaurants/${encodeURIComponent(restaurantId)}`, {
      method: "PATCH",
      body: compactBody({
        name: input.name,
        category: input.category,
        kind: input.kind,
        address: input.address,
        delivery_fee: input.deliveryFee,
        delivery_minutes: input.deliveryMinutes,
        description: input.description,
        artwork: input.artwork,
        is_active: input.isActive,
      }),
    });
    return merchantFromDto(result.data.restaurant);
  }

  async createMenuItem(restaurantId: string, input: CreateMenuItemInput) {
    const result = await this.client.request<Envelope<{ item: ProductDto }>>(
      `/operations/restaurants/${encodeURIComponent(restaurantId)}/menu-items`,
      {
        method: "POST",
        body: compactBody({
          name: input.name,
          category: input.category,
          price: input.price,
          description: input.description,
          artwork: input.artwork,
          is_available: input.isAvailable,
        }),
      },
    );
    return productFromDto(result.data.item);
  }

  async updateMenuItem(
    restaurantId: string,
    itemId: string,
    input: UpdateMenuItemInput,
  ) {
    const result = await this.client.request<Envelope<{ item: ProductDto }>>(
      `/operations/restaurants/${encodeURIComponent(restaurantId)}/menu-items/${encodeURIComponent(itemId)}`,
      {
        method: "PATCH",
        body: compactBody({
          name: input.name,
          category: input.category,
          price: input.price,
          description: input.description,
          artwork: input.artwork,
          is_available: input.isAvailable,
        }),
      },
    );
    return productFromDto(result.data.item);
  }

  async assignStaff(restaurantId: string, userId: string) {
    const result = await this.client.request<
      Envelope<{ restaurant_id: string; user_id: string }>
    >(`/operations/restaurants/${encodeURIComponent(restaurantId)}/staff`, {
      method: "POST",
      body: { user_id: userId },
    });
    return {
      restaurantId: result.data.restaurant_id,
      userId: result.data.user_id,
    };
  }

  async listPreparers(restaurantId?: string, signal?: AbortSignal) {
    const query = restaurantId
      ? `?restaurant_id=${encodeURIComponent(restaurantId)}`
      : "";
    const result = await this.client.request<
      Envelope<{ preparers: PreparerDto[] }>
    >(`/operations/preparers${query}`, { signal });
    return result.data.preparers.map(preparerFromDto);
  }

  async assignPreparer(
    orderId: string,
    preparerId: string,
    reassign = false,
  ) {
    const result = await this.client.request<Envelope<{ order: OrderDto }>>(
      `/orders/${encodeURIComponent(orderId)}/preparer-assignment`,
      {
        method: reassign ? "PATCH" : "POST",
        body: { preparer_id: preparerId },
      },
    );
    return orderFromDto(result.data.order);
  }

  async listKitchenOrders(offset = 0, signal?: AbortSignal, status?: string) {
    const query = new URLSearchParams({
      limit: "20",
      offset: String(offset),
    });
    if (status) query.set("status", status);
    const result = await this.client.request<
      Envelope<{ orders: OrderDto[]; pagination: PaginationDto }>
    >(`/kitchen/orders?${query}`, { signal });
    return {
      items: result.data.orders.map(orderFromDto),
      hasMore: result.data.pagination.has_more,
    };
  }

  async updateKitchenStatus(
    orderId: string,
    status: "preparing" | "ready_for_pickup",
    note?: string,
  ) {
    const result = await this.client.request<Envelope<{ order: OrderDto }>>(
      `/kitchen/orders/${encodeURIComponent(orderId)}/status`,
      {
        method: "PATCH",
        body: note ? { status, note } : { status },
      },
    );
    return orderFromDto(result.data.order);
  }

  async listUsers(
    options: {
      role?: string;
      search?: string;
      limit?: number;
      offset?: number;
    } = {},
    signal?: AbortSignal,
  ) {
    const query = new URLSearchParams({
      limit: String(options.limit ?? 20),
      offset: String(options.offset ?? 0),
    });
    if (options.role) query.set("role", options.role);
    if (options.search) query.set("search", options.search);
    const result = await this.client.request<
      Envelope<{ users: AdminUserDto[]; pagination: PaginationDto }>
    >(`/admin/users?${query}`, { signal });
    return {
      items: result.data.users.map(staffAccountFromDto),
      hasMore: result.data.pagination.has_more,
    };
  }

  async createStaff(input: CreateStaffInput) {
    const result = await this.client.request<Envelope<{ user: AdminUserDto }>>(
      "/admin/staff",
      {
        method: "POST",
        body: compactBody({
          name: input.name,
          email: input.email,
          password: input.password,
          phone: input.phone || null,
          roles: input.roles,
          restaurant_id: input.restaurantId || null,
        }),
      },
    );
    return staffAccountFromDto(result.data.user);
  }

  async updateUserRoles(userId: string, input: UpdateUserRolesInput) {
    const result = await this.client.request<Envelope<{ user: AdminUserDto }>>(
      `/admin/users/${encodeURIComponent(userId)}/roles`,
      {
        method: "PATCH",
        body: compactBody({
          roles: input.roles,
          is_active: input.isActive,
          email_verified: input.emailVerified,
          restaurant_id: input.restaurantId,
        }),
      },
    );
    return staffAccountFromDto(result.data.user);
  }
}
