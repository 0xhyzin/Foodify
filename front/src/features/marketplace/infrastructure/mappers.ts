import type {
  AppNotification,
  Cart,
  CourierOption,
  Merchant,
  Order,
  PreparerOption,
  Product,
} from "../domain/models";
import type {
  CartDto,
  CourierDto,
  MerchantDto,
  NotificationDto,
  OrderDto,
  PreparerDto,
  ProductDto,
} from "./dto";
export const merchantFromDto = (d: MerchantDto): Merchant => ({
  id: d.id,
  name: d.name,
  slug: d.slug,
  kind: d.kind,
  category: d.category,
  tags: d.tags,
  description: d.description ?? "",
  address: d.address ?? "",
  rating: Number(d.rating),
  reviews: d.reviews,
  minutes: d.time,
  deliveryFee: d.delivery_fee,
  artwork: d.artwork,
  logo: d.logo,
});
export const productFromDto = (d: ProductDto): Product => ({
  id: d.id,
  restaurantId: d.restaurant_id,
  name: d.name,
  category: d.category,
  description: d.desc ?? "",
  price: d.price,
  artwork: d.artwork,
  available: d.available,
});
export const cartFromDto = (d: CartDto): Cart => ({
  id: d.id,
  restaurantId: d.restaurant_id,
  revision: d.revision,
  subtotal: d.subtotal,
  deliveryFee: d.delivery_fee,
  total: d.total,
  items: d.items.map((l) => ({
    id: l.id,
    productId: l.menu_item_id,
    name: l.name,
    price: l.price,
    quantity: l.quantity,
    total: l.line_total,
    available: l.available,
  })),
});
export const orderFromDto = (d: OrderDto): Order => ({
  id: d.id,
  restaurantId: d.restaurant_id,
  restaurantName: d.restaurant_name ?? null,
  restaurantAddress: d.restaurant_address ?? null,
  status: d.status,
  paymentMethod: d.payment_method,
  paymentStatus: d.payment_status,
  subtotal: d.subtotal,
  deliveryFee: d.delivery_fee,
  total: d.total,
  createdAt: d.created_at,
  recipientName: d.delivery_address.recipient_name,
  phone: d.delivery_address.phone,
  deliveryAddress: [
    d.delivery_address.city,
    d.delivery_address.area,
    d.delivery_address.street,
    `عمارة ${d.delivery_address.building}`,
    d.delivery_address.floor ? `الدور ${d.delivery_address.floor}` : "",
    d.delivery_address.apartment ? `شقة ${d.delivery_address.apartment}` : "",
  ]
    .filter(Boolean)
    .join("، "),
  deliveryAddressDetails: {
    recipientName: d.delivery_address.recipient_name,
    phone: d.delivery_address.phone,
    city: d.delivery_address.city,
    area: d.delivery_address.area,
    street: d.delivery_address.street,
    building: d.delivery_address.building,
    floor: d.delivery_address.floor ?? null,
    apartment: d.delivery_address.apartment ?? null,
    deliveryNotes: d.delivery_address.delivery_notes ?? null,
  },
  reference: d.payment?.reference ?? "",
  transactionId: d.payment?.transaction_id ?? null,
  providerTransactionId: d.payment?.provider_transaction_id ?? null,
  claimedReference: d.payment?.claimed_reference ?? null,
  simulated: d.payment?.is_simulated ?? false,
  transferRecipient: d.payment?.transfer_recipient ?? null,
  transferRecipientName: d.payment?.transfer_recipient_name ?? null,
  deliveryAssignment: d.delivery_assignment
    ? {
        deliveryPersonId: d.delivery_assignment.delivery_person_id,
        deliveryPersonName: d.delivery_assignment.delivery_person_name,
        status: d.delivery_assignment.status,
        assignedAt: d.delivery_assignment.assigned_at,
        updatedAt: d.delivery_assignment.updated_at,
      }
    : null,
  assignedPreparer: d.assigned_preparer
    ? {
        id: d.assigned_preparer.id,
        name: d.assigned_preparer.name,
      }
    : null,
  items: d.items.map((l) => ({
    productId: l.menu_item_id,
    name: l.name,
    price: l.unit_price,
    quantity: l.quantity,
    total: l.line_total,
  })),
  events: d.events.map((e) => ({
    status: e.status,
    note: e.note,
    createdAt: e.created_at,
  })),
});
export const courierFromDto = (d: CourierDto): CourierOption => ({
  id: d.id,
  name: d.name,
  phone: d.phone,
  activeOrderCount: d.active_order_count,
});
export const preparerFromDto = (d: PreparerDto): PreparerOption => ({
  id: d.id,
  name: d.name,
  phone: d.phone,
  activeOrderCount: d.active_order_count,
});
export const notificationFromDto = (d: NotificationDto): AppNotification => ({
  id: d.id,
  orderId: d.order_id,
  eventType: d.event_type,
  channel: d.channel,
  title: d.title,
  message: d.message,
  deliveryStatus: d.delivery_status,
  readAt: d.read_at,
  createdAt: d.created_at,
});
