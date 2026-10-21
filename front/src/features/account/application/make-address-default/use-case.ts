import type { AccountRepository } from '../../domain/account-repository';
import type { MakeAddressDefaultDto, MakeAddressDefaultResult } from './dto';
import { requireAddressId } from '../../domain/validation';

export function createMakeAddressDefault(repository: AccountRepository) {
  return async function makeAddressDefault(input: MakeAddressDefaultDto): Promise<MakeAddressDefaultResult> {
    return repository.makeAddressDefault(requireAddressId(input));
  };
}
