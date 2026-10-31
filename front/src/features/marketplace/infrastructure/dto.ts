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
  };
  payment: {
    reference: string;
    is_simulated: boolean;
    claimed_reference: string | null;
    transfer_recipient: string | null;
    transfer_recipient_name: string | null;
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
