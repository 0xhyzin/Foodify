import type { AuthRepository } from '../../domain/auth-repository';
import type { RequestPasswordResetDto, RequestPasswordResetResult } from './dto';
import { normalizeEmail } from '../../domain/validation';

export function createRequestPasswordReset(repository: AuthRepository) {
  return async function requestPasswordReset(input: RequestPasswordResetDto): Promise<RequestPasswordResetResult> {
    return repository.requestPasswordReset({ email: normalizeEmail(input.email) });
  };
}
