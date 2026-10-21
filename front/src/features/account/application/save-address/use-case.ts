import type { AccountRepository } from '../../domain/account-repository';
import type { SaveAddressDto, SaveAddressResult } from './dto';
import { normalizeAddress, requireAddressId } from '../../domain/validation';

export function createSaveAddress(repository: AccountRepository) {
  return async function saveAddress(input: SaveAddressDto, id?: string): Promise<SaveAddressResult> {
    return repository.saveAddress(normalizeAddress(input), id === undefined ? undefined : requireAddressId(id));
  };
}
