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
  address?: string;
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
export interface DeliveryAddressDetails {
  recipientName: string;
  phone: string;
  city: string;
  area: string;
  street: string;
  building: string;
  floor: string | null;
  apartment: string | null;
  deliveryNotes: string | null;
}
export interface DeliveryAssignment {
  deliveryPersonId: string;
  deliveryPersonName: string;
  status: string;
  assignedAt: string;
  updatedAt: string;
}
export interface PreparerSummary {
  id: string;
  name: string;
}
export interface CourierOption {
  id: string;
  name: string;
  phone: string | null;
  activeOrderCount: number;
}
export interface PreparerOption {
  id: string;
  name: string;
  phone: string | null;
  activeOrderCount: number;
}
export interface AppNotification {
  id: string;
  orderId: string;
  eventType: string;
  channel: string;
  title: string;
  message: string;
  deliveryStatus: string;
  readAt: string | null;
  createdAt: string;
}
export interface NotificationPage {
  items: AppNotification[];
  unreadCount: number;
  hasMore: boolean;
}
export interface CreateRestaurantInput {
  name: string;
  category: string;
  kind: MerchantKind;
  address: string;
  deliveryFee: Money;
  deliveryMinutes: number;
  description?: string;
  artwork?: string;
  isActive?: boolean;
}
export interface UpdateRestaurantInput {
  name?: string;
  category?: string;
  kind?: MerchantKind;
  address?: string;
  deliveryFee?: Money;
  deliveryMinutes?: number;
  description?: string | null;
  artwork?: string;
  isActive?: boolean;
}
export interface CreateMenuItemInput {
  name: string;
  category: string;
  price: Money;
  description?: string;
  artwork?: string;
  isAvailable?: boolean;
}
export interface UpdateMenuItemInput {
  name?: string;
  category?: string;
  price?: Money;
  description?: string | null;
  artwork?: string;
  isAvailable?: boolean;
}
export type RoleCode =
  | "customer"
  | "courier"
  | "order_preparer"
  | "restaurant_manager"
  | "operations_manager"
  | "admin";
export interface StaffAccount {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  isActive: boolean;
  emailVerified: boolean;
  roles: string[];
  managedRestaurantIds: string[];
  createdAt: string;
}
export interface CreateStaffInput {
  name: string;
  email: string;
  password: string;
  phone?: string | null;
  roles: RoleCode[];
  restaurantId?: string | null;
}
export interface UpdateUserRolesInput {
  roles: RoleCode[];
  isActive?: boolean;
  emailVerified?: boolean;
  restaurantId?: string | null;
}
export interface OrderEvent {
  status: string;
  createdAt: string;
  note: string | null;
}
export interface Order {
  id: string;
  restaurantId: string;
  restaurantName: string | null;
  restaurantAddress: string | null;
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
  deliveryAddressDetails: DeliveryAddressDetails;
  reference: string;
  transactionId: string | null;
  providerTransactionId: string | null;
  claimedReference: string | null;
  simulated: boolean;
  transferRecipient: string | null;
  transferRecipientName: string | null;
  deliveryAssignment: DeliveryAssignment | null;
  assignedPreparer: PreparerSummary | null;
  items: {
    productId: string;
    name: string;
    price: Money;
    quantity: number;
    total: Money;
  }[];
  events: OrderEvent[];
}
