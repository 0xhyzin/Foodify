import type { AccountRepository } from '../../domain/account-repository';
import type { RemoveAddressDto, RemoveAddressResult } from './dto';
import { requireAddressId } from '../../domain/validation';

export function createRemoveAddress(repository: AccountRepository) {
  return async function removeAddress(input: RemoveAddressDto): Promise<RemoveAddressResult> {
    return repository.removeAddress(requireAddressId(input));
  };
}
