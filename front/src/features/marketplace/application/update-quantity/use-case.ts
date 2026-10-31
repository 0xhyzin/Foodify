import type { CartRepository } from "../../domain/cart-repository";
import { AppError } from "@/shared/domain/app-error";
export function createUpdateQuantity(repository: CartRepository) {
  return (merchantId: string, lineId: string, quantity: number) => {
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99)
      throw new AppError("quantity_limit", "الكمية المتاحة من ١ إلى ٩٩.");
    return repository.update(merchantId, lineId, quantity);
  };
}
