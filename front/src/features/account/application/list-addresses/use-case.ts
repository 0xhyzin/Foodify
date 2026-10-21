import type { AccountRepository } from '../../domain/account-repository';
import type { ListAddressesResult } from './dto';

export function createListAddresses(repository: AccountRepository) {
  return async function listAddresses(): Promise<ListAddressesResult> {
    return repository.listAddresses();
  };
}
