import { AppError } from '../../shared/domain/app-error';
import type { BrowserSessionDto } from './contracts';

export function parseBrowserSession(value: unknown): BrowserSessionDto {
  const session = value as Partial<BrowserSessionDto> | null;
  const user = session?.user;
  if (!session || typeof session.access_token !== 'string' || !session.access_token.trim()
    || session.token_type !== 'bearer' || typeof session.expires_in !== 'number'
    || !Number.isFinite(session.expires_in) || session.expires_in <= 0
    || !user || typeof user.id !== 'string' || typeof user.name !== 'string'
    || typeof user.email !== 'string'
    || (user.phone !== null && typeof user.phone !== 'string')
    || typeof user.email_verified !== 'boolean' || typeof user.profile_complete !== 'boolean'
    || (user.default_address_id !== null && typeof user.default_address_id !== 'string')
    || !Array.isArray(user.roles) || !user.roles.every(role => typeof role === 'string')
    || !Array.isArray(user.permissions) || !user.permissions.every(permission => typeof permission === 'string')
    || typeof user.created_at !== 'string') {
    throw new AppError('invalid_response', 'استجابة تسجيل الدخول غير مكتملة. جرّب مرة تانية.');
  }
  return session as BrowserSessionDto;
}
