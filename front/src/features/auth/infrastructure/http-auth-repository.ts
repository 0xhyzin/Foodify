import type { BackendUserDto, BrowserSessionDto, BrowserSessionPort, HttpClient } from '../../../infrastructure/http/contracts';
import type { UserProfile } from '../../account/domain/models';
import { toUserProfile } from '../../account/infrastructure/mappers/user-profile-mapper';
import type { AuthRepository } from '../domain/auth-repository';
import type { CompleteProviderSignInInput, EmailInput, OAuthProvider, ResetPasswordInput, SignInInput, SignUpInput, TokenInput } from '../domain/models';
import type { OAuthFlowPort } from '../domain/oauth-flow';
import type { ConfirmEmailRequestDto, EmailRequestDto, MessageResponseDto, ResetPasswordRequestDto, SignInRequestDto, SignUpRequestDto } from './dto/auth-dto';

export class HttpAuthRepository implements AuthRepository {
  constructor(
    private readonly client: HttpClient,
    private readonly session: BrowserSessionPort,
    private readonly oauth: OAuthFlowPort,
  ) {}

  async signIn(input: SignInInput): Promise<UserProfile> {
    this.oauth.cancel();
    const body: SignInRequestDto = { email: input.email, password: input.password };
    const dto = await this.client.request<BrowserSessionDto>('/auth/browser/login', {
      method: 'POST', body, authenticated: false,
    });
    const user = toUserProfile(dto.user);
    this.session.accept(dto);
    return user;
  }

  async signUp(input: SignUpInput): Promise<void> {
    const body: SignUpRequestDto = { name: input.name, email: input.email, password: input.password };
    await this.client.request<MessageResponseDto>('/auth/register', { method: 'POST', body, authenticated: false });
  }

  async confirmEmail(input: TokenInput): Promise<void> {
    const body: ConfirmEmailRequestDto = { token: input.token };
    await this.client.request<MessageResponseDto>('/auth/verify-email', { method: 'POST', body, authenticated: false });
  }

  async resendVerification(input: EmailInput): Promise<void> {
    const body: EmailRequestDto = { email: input.email };
    await this.client.request<MessageResponseDto>('/auth/resend-verification', { method: 'POST', body, authenticated: false });
  }

  async requestPasswordReset(input: EmailInput): Promise<void> {
    const body: EmailRequestDto = { email: input.email };
    await this.client.request<MessageResponseDto>('/auth/forgot-password', { method: 'POST', body, authenticated: false });
  }

  async resetPassword(input: ResetPasswordInput): Promise<void> {
    const body: ResetPasswordRequestDto = { token: input.token, password: input.password };
    await this.client.request<MessageResponseDto>('/auth/reset-password', { method: 'POST', body, authenticated: false });
    this.session.clear();
  }

  async signInWithProvider(provider: OAuthProvider): Promise<UserProfile> {
    return this.oauth.start(provider);
  }

  async completeProviderSignIn(input: CompleteProviderSignInInput): Promise<UserProfile> {
    return this.oauth.complete(input.ticket);
  }

  cancelProviderSignIn(): void {
    this.oauth.cancel();
  }

  onSessionInvalidated(listener: () => void): () => void {
    return this.session.subscribe(() => {
      if (!this.session.current()) listener();
    });
  }

  async signOut(): Promise<void> {
    this.oauth.cancel();
    await this.session.signOut();
  }

  async getSession(): Promise<UserProfile | null> {
    const session = this.session.current() ?? await this.session.restore();
    if (!session) return null;
    return toUserProfile(await this.client.request<BackendUserDto>('/users/me'));
  }
}
