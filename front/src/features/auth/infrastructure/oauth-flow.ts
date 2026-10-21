import { AppError } from '../../../shared/domain/app-error';
import type { HttpClient } from '../../../infrastructure/http/contracts';
import type { UserProfile } from '../../account/domain/models';
import { toUserProfile } from '../../account/infrastructure/mappers/user-profile-mapper';
import type { CompleteProviderSignInInput, OAuthProvider } from '../domain/models';
import type { OAuthFlowPort } from '../domain/oauth-flow';
import type { BrowserSessionDto } from '../../../infrastructure/http/contracts';

interface OAuthStartDto {
  authorization_url: string;
}

const verifierKey = (provider: OAuthProvider) => `foodify.oauth.verifier.${provider}`;

function randomVerifier(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return toBase64Url(bytes);
}

function toBase64Url(bytes: Uint8Array): string {
  let value = '';
  bytes.forEach(byte => { value += String.fromCharCode(byte); });
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

async function challengeFor(verifier: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

export class BrowserOAuthFlow implements OAuthFlowPort {
  private revision = 0;

  constructor(private readonly client: HttpClient, private readonly acceptSession: (session: BrowserSessionDto) => void) {}

  async start(provider: OAuthProvider): Promise<never> {
    this.cancel();
    const startedAt = this.revision;
    try {
      const verifier = randomVerifier();
      const challenge = await challengeFor(verifier);
      if (startedAt !== this.revision) throw new AppError('oauth_session_missing', 'ابدأ تسجيل الدخول من جديد.');
      sessionStorage.setItem(verifierKey(provider), verifier);
      const result = await this.client.request<OAuthStartDto>(`/auth/oauth/${provider}/start`, {
        method: 'POST',
        body: { binding_challenge: challenge },
        authenticated: false,
      });
      if (startedAt !== this.revision) throw new AppError('oauth_session_missing', 'ابدأ تسجيل الدخول من جديد.');
      const url = new URL(result.authorization_url);
      const validProvider = provider === 'google'
        ? url.hostname === 'accounts.google.com' && url.pathname === '/o/oauth2/v2/auth'
        : url.hostname === 'www.facebook.com' && /^\/v\d+\.\d+\/dialog\/oauth$/.test(url.pathname);
      if (url.protocol !== 'https:' || url.username || url.password || url.port || !validProvider) {
        throw new AppError('invalid_response', 'رابط تسجيل الدخول غير صالح. جرّب مرة تانية.');
      }
      window.location.assign(url.href);
    } catch (error) {
      if (startedAt === this.revision) this.cancel();
      if (error instanceof AppError) throw error;
      throw new AppError('oauth_unavailable', 'تعذر بدء تسجيل الدخول. تأكد إن المتصفح يسمح بتخزين بيانات الجلسة.');
    }
    return new Promise<never>(() => undefined);
  }

  async complete(ticket: string): Promise<UserProfile> {
    const startedAt = this.revision;
    const provider = this.providerForTicket();
    if (!provider) throw new AppError('oauth_session_missing', 'جلسة تسجيل الدخول انتهت. ابدأ من جديد.');
    const verifier = this.readVerifier(provider);
    if (!verifier) throw new AppError('oauth_session_missing', 'جلسة تسجيل الدخول انتهت. ابدأ من جديد.');
    try {
      const dto = await this.client.request<BrowserSessionDto>('/auth/browser/oauth/complete', {
        method: 'POST',
        body: { ticket, binding_verifier: verifier },
        authenticated: false,
      });
      if (startedAt !== this.revision) throw new AppError('oauth_session_missing', 'ابدأ تسجيل الدخول من جديد.');
      const user = toUserProfile(dto.user);
      this.acceptSession(dto);
      return user;
    } finally {
      if (startedAt === this.revision) this.cancel();
    }
  }

  cancel(): void {
    this.revision += 1;
    try {
      sessionStorage.removeItem(verifierKey('google'));
      sessionStorage.removeItem(verifierKey('facebook'));
    } catch {
      // Storage may be disabled; there is then no verifier available to clear.
    }
  }

  private providerForTicket(): OAuthProvider | null {
    // The callback ticket is opaque. The verifier is scoped to a provider, so inspect
    // only the two known session keys and never parse or trust values from the URL.
    if (this.readVerifier('google')) return 'google';
    if (this.readVerifier('facebook')) return 'facebook';
    return null;
  }

  private readVerifier(provider: OAuthProvider): string | null {
    try {
      return sessionStorage.getItem(verifierKey(provider));
    } catch {
      throw new AppError('oauth_storage_unavailable', 'المتصفح مانع تخزين بيانات الجلسة. اسمح بتخزينها وابدأ تسجيل الدخول من جديد.');
    }
  }
}

export type CompleteProviderSignIn = (input: CompleteProviderSignInInput) => Promise<UserProfile>;
