import type { BackendUserDto } from '../../../../infrastructure/http/contracts';
import { AppError } from '../../../../shared/domain/app-error';
import type { UserProfile } from '../../domain/models';

/** Keep backend naming and extra private implementation fields outside the UI. */
export function toUserProfile(dto: BackendUserDto): UserProfile {
  if (!dto || typeof dto !== 'object'
    || typeof dto.id !== 'string' || typeof dto.name !== 'string'
    || typeof dto.email !== 'string'
    || (dto.phone !== null && typeof dto.phone !== 'string')
    || typeof dto.email_verified !== 'boolean'
    || typeof dto.profile_complete !== 'boolean'
    || (dto.default_address_id !== null && typeof dto.default_address_id !== 'string')
    || !Array.isArray(dto.roles) || !dto.roles.every(role => typeof role === 'string')) {
    throw new AppError('invalid_response', 'استجابة بيانات الحساب غير مكتملة. جرّب مرة تانية.');
  }

  return {
    id: dto.id,
    name: dto.name,
    email: dto.email,
    phoneNumber: dto.phone,
    emailVerified: dto.email_verified,
    profileComplete: dto.profile_complete,
    defaultAddressId: dto.default_address_id,
    roles: [...dto.roles],
  };
}
