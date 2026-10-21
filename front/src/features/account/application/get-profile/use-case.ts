import type { AccountRepository } from '../../domain/account-repository';
import type { GetProfileResult } from './dto';

export function createGetProfile(repository: AccountRepository) {
  return async function getProfile(): Promise<GetProfileResult> {
    return repository.getProfile();
  };
}
