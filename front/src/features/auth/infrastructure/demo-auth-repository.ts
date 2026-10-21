import { DemoStore, simulateLatency } from '../../../infrastructure/demo/demo-store';
import { AppError } from '../../../shared/domain/app-error';
import type { UserProfile } from '../../account/domain/models';
import type { AuthRepository } from '../domain/auth-repository';
import type { CompleteProviderSignInInput, EmailInput, OAuthProvider, ResetPasswordInput, SignInInput, SignUpInput, TokenInput } from '../domain/models';

/** Demonstration adapter: never checks, stores, or sends passwords. */
export class DemoAuthRepository implements AuthRepository {
  private readonly listeners = new Set<() => void>();

  constructor(private readonly store: DemoStore) {}

  async signIn(input: SignInInput): Promise<UserProfile> {
    await simulateLatency();
    const account = this.store.findByEmail(input.email);
    if (!account) {
      throw new AppError('invalid_credentials', 'البريد أو كلمة المرور غير صحيحة في النسخة التجريبية. جرّب حساب العرض أو اعمل حساب جديد.');
    }
    if (!account.emailVerified) {
      throw new AppError('email_not_verified', 'أكد بريدك الإلكتروني الأول، وبعدها تقدر تسجّل الدخول.');
    }
    this.store.activeUserId = account.id;
    return this.store.toProfile(account);
  }

  async signUp(input: SignUpInput): Promise<void> {
    await simulateLatency();
    if (this.store.findByEmail(input.email)) {
      throw new AppError('account_exists', 'البريد ده مسجّل بالفعل في العرض التجريبي. سجّل الدخول أو جرّب بريد تاني.', { email: 'البريد ده مسجّل بالفعل.' });
    }
    const id = crypto.randomUUID();
    this.store.accounts.set(id, {
      id, name: input.name, email: input.email, phoneNumber: null,
      emailVerified: false, defaultAddressId: null, roles: ['customer'], addresses: [],
    });
    this.store.issueToken(input.email, 'verification');
  }

  async confirmEmail(input: TokenInput): Promise<void> {
    await simulateLatency();
    const account = this.store.consumeToken(input.token, 'verification');
    account.emailVerified = true;
  }

  async resendVerification(input: EmailInput): Promise<void> {
    await simulateLatency();
    const account = this.store.findByEmail(input.email);
    if (account && !account.emailVerified) this.store.issueToken(account.email, 'verification');
  }

  async requestPasswordReset(input: EmailInput): Promise<void> {
    await simulateLatency();
    this.store.issueToken(input.email, 'reset');
  }

  async resetPassword(input: ResetPasswordInput): Promise<void> {
    await simulateLatency();
    this.store.consumeToken(input.token, 'reset');
    this.invalidateSession();
  }

  async signInWithProvider(provider: OAuthProvider): Promise<UserProfile> {
    await simulateLatency(500);
    const email = `${provider}.demo@example.com`;
    let account = this.store.findByEmail(email);
    if (!account) {
      const id = crypto.randomUUID();
      account = {
        id, name: provider === 'google' ? 'مريم أحمد' : 'مريم محمد', email,
        phoneNumber: null, emailVerified: true, defaultAddressId: null,
        roles: ['customer'], addresses: [],
      };
      this.store.accounts.set(id, account);
    }
    this.store.activeUserId = account.id;
    return this.store.toProfile(account);
  }

  async completeProviderSignIn(_input: CompleteProviderSignInInput): Promise<UserProfile> {
    return this.signInWithProvider('google');
  }

  cancelProviderSignIn(): void {
    // Demo sign-in never leaves the page or stores a provider verifier.
  }

  onSessionInvalidated(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  }

  private invalidateSession(): void {
    this.store.activeUserId = null;
    this.listeners.forEach(listener => listener());
  }

  async signOut(): Promise<void> {
    await simulateLatency(120);
    this.invalidateSession();
  }

  async getSession(): Promise<UserProfile | null> {
    await simulateLatency(80);
    const account = this.store.activeUserId ? this.store.accounts.get(this.store.activeUserId) : undefined;
    return account ? this.store.toProfile(account) : null;
  }
}
