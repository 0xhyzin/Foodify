export type MerchantKind = "restaurant" | "dessert" | "grocery";
export type Money = string;
export interface Page<T> {
  items: T[];
  hasMore: boolean;
}
export interface Category {
  code: string;
  name: string;
  artwork: string;
}
export interface Merchant {
  id: string;
  slug: string | null;
  name: string;
  kind: MerchantKind;
  category: string;
  tags: string[];
  description: string;
  rating: number;
  reviews: number;
  minutes: number;
  deliveryFee: Money;
  artwork: string;
  logo: string | null;
}
export interface Product {
  id: string;
  restaurantId: string;
  name: string;
  category: string;
  description: string;
  price: Money;
  artwork: string;
  available: boolean;
}
export interface CatalogQuery {
  search?: string;
  category?: string;
  kind?: MerchantKind;
  sort?: "rating" | "fastest" | "delivery_fee";
  freeDelivery?: boolean;
  maxMinutes?: number;
  offset?: number;
}
export interface CartLine {
  id: string;
  productId: string;
  name: string;
  price: Money;
  quantity: number;
  total: Money;
  available: boolean;
}
export interface Cart {
  id: string | null;
  restaurantId: string;
  revision: number;
  items: CartLine[];
  subtotal: Money;
  deliveryFee: Money;
  total: Money;
}
export type PaymentMethodCode =
  | "card"
  | "vodafone_cash"
  | "orange_cash"
  | "instapay"
  | "cash"
  | "simulated";
export interface PaymentMethod {
  code: PaymentMethodCode;
  label: string;
  enabled: boolean;
  recipient?: string | null;
  recipientName?: string | null;
}
export interface CheckoutInput {
  restaurantId: string;
  addressId: string;
  method: PaymentMethodCode;
  expectedTotal: Money;
  cartRevision: number;
}
export interface OrderEvent {
  status: string;
  createdAt: string;
  note: string | null;
}
export interface Order {
  id: string;
  restaurantId: string;
  status: string;
  paymentMethod: string;
  paymentStatus: string;
  subtotal: Money;
  deliveryFee: Money;
  total: Money;
  createdAt: string;
  recipientName: string;
  phone: string;
  deliveryAddress: string;
  reference: string;
  claimedReference: string | null;
  simulated: boolean;
  transferRecipient: string | null;
  transferRecipientName: string | null;
  items: {
    productId: string;
    name: string;
    price: Money;
    quantity: number;
    total: Money;
  }[];
  events: OrderEvent[];
}
