import type { AuthRepository } from '../../domain/auth-repository';
import type { GetSessionResult } from './dto';

export function createGetSession(repository: AuthRepository) {
  return async function getSession(): Promise<GetSessionResult> {
    return repository.getSession();
  };
}
