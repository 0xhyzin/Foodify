import type { AuthRepository } from '../../domain/auth-repository';
import type { SignOutResult } from './dto';

export function createSignOut(repository: AuthRepository) {
  return async function signOut(): Promise<SignOutResult> {
    return repository.signOut();
  };
}
