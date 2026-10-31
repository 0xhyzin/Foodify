import type { PaymentRepository } from "../../domain/payment-repository";
import { AppError } from "@/shared/domain/app-error";
export function createStartPayment(repository: PaymentRepository) {
  return async (id: string) => {
    const result = await repository.start(id);
    const url = new URL(result.url);
    if (
      url.origin !== "https://accept.paymob.com" ||
      url.pathname !== "/unifiedcheckout/" ||
      url.username ||
      url.password
    ) {
      throw new AppError(
        "invalid_payment_destination",
        "رابط بوابة الدفع غير صالح. تواصل مع الدعم برقم الطلب.",
      );
    }
    return result;
  };
}
