import type { AuthRepository } from '../../domain/auth-repository';
import type { SignInDto, SignInResult } from './dto';
import { normalizeEmail, validatePassword } from '../../domain/validation';

export function createSignIn(repository: AuthRepository) {
  return async function signIn(input: SignInDto): Promise<SignInResult> {
    return repository.signIn({ email: normalizeEmail(input.email), password: validatePassword(input.password, false) });
  };
}
