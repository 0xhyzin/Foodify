import type { AuthRepository } from '../../domain/auth-repository';
import type { ConfirmEmailDto, ConfirmEmailResult } from './dto';
import { requireToken } from '../../domain/validation';

export function createConfirmEmail(repository: AuthRepository) {
  return async function confirmEmail(input: ConfirmEmailDto): Promise<ConfirmEmailResult> {
    return repository.confirmEmail({ token: requireToken(input.token) });
  };
}
