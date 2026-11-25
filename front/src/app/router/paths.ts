import type { UserProfile } from '@/features/account/domain/models';
import { primaryPortalPath } from '@/features/marketplace/presentation/status-labels';
export function accountDestination(user: UserProfile) {
  if (!user.phoneNumber) return '/onboarding/profile';
  if (!user.defaultAddressId) return '/onboarding/address';
  return '/account';
}
export function loginDestination(user: UserProfile) {
  return primaryPortalPath(user.roles) ?? accountDestination(user);
}
