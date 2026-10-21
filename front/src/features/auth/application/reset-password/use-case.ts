import type { AuthRepository } from '../../domain/auth-repository';
import type { ResetPasswordDto, ResetPasswordResult } from './dto';
import { requireToken, validatePassword } from '../../domain/validation';

export function createResetPassword(repository: AuthRepository) {
  return async function resetPassword(input: ResetPasswordDto): Promise<ResetPasswordResult> {
    return repository.resetPassword({ token: requireToken(input.token), password: validatePassword(input.password, true) });
  };
}
