import type { AuthRepository } from '../../domain/auth-repository';
import type { SignInWithProviderDto, SignInWithProviderResult } from './dto';

export function createSignInWithProvider(repository: AuthRepository) {
  return async function signInWithProvider(input: SignInWithProviderDto): Promise<SignInWithProviderResult> {
    return repository.signInWithProvider(input);
  };
}
