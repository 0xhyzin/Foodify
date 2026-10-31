import type { CheckoutInput } from "../../domain/models";
import type { OrderRepository } from "../../domain/order-repository";
import { AppError } from "@/shared/domain/app-error";
export function createCheckout(repository: OrderRepository) {
  return (input: CheckoutInput, key: string) => {
    if (!input.restaurantId || !input.addressId || !key)
      throw new AppError(
        "invalid_checkout",
        "اختار عنوان التوصيل ووسيلة الدفع.",
      );
    return repository.checkout(input, key);
  };
}
