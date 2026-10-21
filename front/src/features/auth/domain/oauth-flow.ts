import type { OAuthProvider } from './models';

export interface OAuthFlowPort {
  start(provider: OAuthProvider): Promise<never>;
  complete(ticket: string): Promise<import('../../account/domain/models').UserProfile>;
  cancel(): void;
}
