import type { PaymentRepository } from "../../domain/payment-repository";
import { AppError } from "@/shared/domain/app-error";
export function createStartPayment(repository: PaymentRepository) {
  return async (id: string) => {
    const result = await repository.start(id);
    let url: URL;
    try {
      url = new URL(result.url);
    } catch {
      throw new AppError(
        "invalid_payment_destination",
        "رابط بوابة الدفع غير صالح. تواصل مع الدعم برقم الطلب.",
      );
    }
    const allowedDestination =
      (url.origin === "https://eg.checkout.paymob.com" && url.pathname === "/") ||
      (url.origin === "https://accept.paymob.com" && url.pathname === "/unifiedcheckout/");
    if (
      !allowedDestination ||
      url.username ||
      url.password ||
      url.hash ||
      url.searchParams.getAll("publicKey").length !== 1 ||
      !url.searchParams.get("publicKey")?.trim() ||
      url.searchParams.getAll("clientSecret").length !== 1 ||
      !url.searchParams.get("clientSecret")?.trim()
    ) {
      throw new AppError(
        "invalid_payment_destination",
        "رابط بوابة الدفع غير صالح. تواصل مع الدعم برقم الطلب.",
      );
    }
    const expiresAt = Date.parse(result.expiresAt);
    if (!Number.isFinite(expiresAt) || expiresAt <= Date.now())
      throw new AppError(
        "payment_expired",
        "صلاحية رابط الدفع انتهت. راجع حالة الطلب قبل ما تكمل.",
      );
    return { ...result, url: url.href };
  };
}
