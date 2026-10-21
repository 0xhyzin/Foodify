import type { AccountRepository } from '../../domain/account-repository';
import type { UpdateProfileDto, UpdateProfileResult } from './dto';
import { normalizeEgyptianPhone } from '../../domain/validation';
import { normalizeName } from '../../../auth/domain/validation';

export function createUpdateProfile(repository: AccountRepository) {
  return async function updateProfile(input: UpdateProfileDto): Promise<UpdateProfileResult> {
    return repository.updateProfile({ name: normalizeName(input.name), phoneNumber: normalizeEgyptianPhone(input.phoneNumber) });
  };
}
