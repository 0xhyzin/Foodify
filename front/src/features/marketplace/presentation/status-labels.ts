export const orderLabels: Record<string, string> = {
  awaiting_payment: "بانتظار الدفع",
  pending: "في انتظار قبول المطعم",
  accepted: "تم قبول الطلب",
  rejected: "مرفوض من المطعم",
  preparing: "جاري التحضير",
  ready_for_pickup: "جاهز للاستلام",
  picked_up: "في الطريق ليك",
  delivered: "تم التسليم بالهنا",
  cancelled: "تم الإلغاء",
};
export const paymentLabels: Record<string, string> = {
  pending: "بانتظار تأكيد بوابة الدفع",
  initializing: "جارٍ تجهيز الدفع",
  initialization_unknown: "إعداد الدفع يحتاج مراجعة من الدعم",
  paid: "مدفوع",
  failed: "الدفع لم يكتمل",
  refunded: "تم رد أو إلغاء التحصيل",
  awaiting_transfer: "بانتظار التحويل",
  pending_review: "التحويل قيد المراجعة",
  rejected: "التحويل محتاج مراجعة البيانات",
  due_on_delivery: "الدفع عند الاستلام",
  simulated: "دفع تجريبي — بدون تحصيل",
};
export const stages = [
  "pending",
  "accepted",
  "preparing",
  "ready_for_pickup",
  "picked_up",
  "delivered",
];

export function nextOrderStage(status: string): string | undefined {
  const index = stages.indexOf(status);
  return index >= 0 ? stages[index + 1] : undefined;
}

export function nextManagerStage(
  status: string,
): "preparing" | "ready_for_pickup" | undefined {
  if (status === "accepted") return "preparing";
  if (status === "preparing") return "ready_for_pickup";
  return undefined;
}

export function nextKitchenStage(
  status: string,
): "preparing" | "ready_for_pickup" | undefined {
  if (status === "accepted") return "preparing";
  if (status === "preparing") return "ready_for_pickup";
  return undefined;
}

export function nextCourierStage(
  status: string,
): "PICKED_UP" | "DELIVERED" | undefined {
  if (status === "ready_for_pickup") return "PICKED_UP";
  if (status === "picked_up") return "DELIVERED";
  return undefined;
}

export const notificationEventLabels: Record<string, string> = {
  order_accepted: "تم قبول الطلب",
  order_rejected: "تم رفض الطلب",
  order_preparing: "بدأ التحضير",
  order_ready_for_pickup: "جاهز للاستلام",
  delivery_assigned: "تم تعيين مندوب",
  delivery_reassigned: "تم تغيير المندوب",
  order_picked_up: "في الطريق للعميل",
  order_delivered: "تم التسليم",
  payment_failed: "تعذّر الدفع",
  order_cancelled: "تم إلغاء الطلب",
  order_assigned_to_preparer: "طلب جديد للتحضير",
  order_ready_for_courier_pickup: "جاهز للاستلام من المطعم",
};

const MANAGER_ROLES = new Set([
  "admin",
  "operations_manager",
  "restaurant_manager",
]);
const KITCHEN_ROLES = new Set([
  "order_preparer",
  "restaurant_manager",
  "operations_manager",
  "admin",
]);
const COURIER_ROLES = new Set(["courier", "admin"]);

export function hasManagerRole(roles: readonly string[] | undefined): boolean {
  return Boolean(roles?.some((role) => MANAGER_ROLES.has(role)));
}

export function hasKitchenRole(roles: readonly string[] | undefined): boolean {
  return Boolean(roles?.some((role) => KITCHEN_ROLES.has(role)));
}

export function hasCourierRole(roles: readonly string[] | undefined): boolean {
  return Boolean(roles?.some((role) => COURIER_ROLES.has(role)));
}

export function primaryPortalPath(roles: readonly string[] | undefined): string | null {
  if (!roles?.length) return null;
  if (roles.some((r) => ["admin", "operations_manager", "restaurant_manager"].includes(r))) {
    return "/operations";
  }
  if (roles.includes("order_preparer")) return "/kitchen";
  if (roles.includes("courier")) return "/delivery";
  return null;
}
