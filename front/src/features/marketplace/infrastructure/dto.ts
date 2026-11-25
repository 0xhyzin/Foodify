export interface Envelope<T> {
  data: T;
}
export interface PaginationDto {
  has_more: boolean;
}
export interface MerchantDto {
  id: string;
  name: string;
  slug: string | null;
  kind: "restaurant" | "dessert" | "grocery";
  category: string;
  tags: string[];
  description: string | null;
  address?: string;
  rating: string;
  reviews: number;
  time: number;
  delivery_fee: string;
  artwork: string;
  logo: string | null;
}
export interface ProductDto {
  id: string;
  restaurant_id: string;
  name: string;
  category: string;
  desc: string | null;
  price: string;
  artwork: string;
  available: boolean;
}
export interface CartDto {
  id: string | null;
  restaurant_id: string;
  revision: number;
  subtotal: string;
  delivery_fee: string;
  total: string;
  items: {
    id: string;
    menu_item_id: string;
    name: string;
    price: string;
    quantity: number;
    line_total: string;
    available: boolean;
  }[];
}
export interface OrderDto {
  id: string;
  restaurant_id: string;
  restaurant_name?: string | null;
  restaurant_address?: string | null;
  status: string;
  payment_method: string;
  payment_status: string;
  subtotal: string;
  delivery_fee: string;
  total: string;
  created_at: string;
  delivery_address: {
    recipient_name: string;
    phone: string;
    city: string;
    area: string;
    street: string;
    building: string;
    floor?: string | null;
    apartment?: string | null;
    delivery_notes?: string | null;
  };
  payment: {
    reference: string;
    transaction_id?: string | null;
    provider_transaction_id?: string | null;
    is_simulated: boolean;
    claimed_reference: string | null;
    transfer_recipient: string | null;
    transfer_recipient_name: string | null;
  } | null;
  delivery_assignment?: {
    delivery_person_id: string;
    delivery_person_name: string;
    status: string;
    assigned_at: string;
    updated_at: string;
  } | null;
  assigned_preparer?: {
    id: string;
    name: string;
  } | null;
  items: {
    menu_item_id: string;
    name: string;
    unit_price: string;
    quantity: number;
    line_total: string;
  }[];
  events: { status: string; note: string | null; created_at: string }[];
}
export interface CourierDto {
  id: string;
  name: string;
  phone: string | null;
  active_order_count: number;
}
export interface PreparerDto {
  id: string;
  name: string;
  phone: string | null;
  active_order_count: number;
}
export interface NotificationDto {
  id: string;
  order_id: string;
  event_type: string;
  channel: string;
  title: string;
  message: string;
  delivery_status: string;
  read_at: string | null;
  created_at: string;
}
export interface AssignDeliveryResultDto {
  order_id: string;
  delivery_person_id: string;
  delivery_person_name: string;
  assignment_status: string;
  assigned_at: string;
}
export interface ReassignDeliveryResultDto {
  order_id: string;
  previous_delivery_person_id: string;
  new_delivery_person_id: string;
  new_delivery_person_name: string;
  assignment_status: string;
  updated_at: string;
}
export interface UpdateDeliveryStatusResultDto {
  order_id: string;
  previous_status: string;
  current_status: string;
  order: OrderDto;
}
export interface AdminUserDto {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  is_active: boolean;
  email_verified: boolean;
  roles: string[];
  managed_restaurant_ids?: string[];
  created_at: string;
}
