import type { AuthRepository } from '../../domain/auth-repository';
import type { SignUpDto, SignUpResult } from './dto';
import { normalizeEmail, normalizeName, validatePassword } from '../../domain/validation';

export function createSignUp(repository: AuthRepository) {
  return async function signUp(input: SignUpDto): Promise<SignUpResult> {
    return repository.signUp({ name: normalizeName(input.name), email: normalizeEmail(input.email), password: validatePassword(input.password, true) });
  };
}
