import type { UserProfile } from '../../account/domain/models';
import type { CompleteProviderSignInInput, EmailInput, OAuthProvider, ResetPasswordInput, SignInInput, SignUpInput, TokenInput } from './models';

export interface AuthRepository {
  signIn(input: SignInInput): Promise<UserProfile>;
  signUp(input: SignUpInput): Promise<void>;
  confirmEmail(input: TokenInput): Promise<void>;
  resendVerification(input: EmailInput): Promise<void>;
  requestPasswordReset(input: EmailInput): Promise<void>;
  resetPassword(input: ResetPasswordInput): Promise<void>;
  signInWithProvider(provider: OAuthProvider): Promise<UserProfile>;
  completeProviderSignIn(input: CompleteProviderSignInInput): Promise<UserProfile>;
  cancelProviderSignIn(): void;
  onSessionInvalidated(listener: () => void): () => void;
  signOut(): Promise<void>;
  getSession(): Promise<UserProfile | null>;
}
