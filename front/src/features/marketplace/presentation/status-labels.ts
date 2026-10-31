export const orderLabels: Record<string, string> = {
  awaiting_payment: "بانتظار الدفع",
  placed: "تم تأكيد الطلب",
  preparing: "بيتحضّر دلوقتي",
  ready: "جاهز للاستلام",
  out_for_delivery: "في الطريق ليك",
  delivered: "وصل بالهنا",
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
  "placed",
  "preparing",
  "ready",
  "out_for_delivery",
  "delivered",
];
