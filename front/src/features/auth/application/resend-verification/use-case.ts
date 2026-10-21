import type { AuthRepository } from '../../domain/auth-repository';
import type { ResendVerificationDto, ResendVerificationResult } from './dto';
import { normalizeEmail } from '../../domain/validation';

export function createResendVerification(repository: AuthRepository) {
  return async function resendVerification(input: ResendVerificationDto): Promise<ResendVerificationResult> {
    return repository.resendVerification({ email: normalizeEmail(input.email) });
  };
}
