import type { UserProfile } from '@/features/account/domain/models';
export function accountDestination(user: UserProfile) {
  if (!user.phoneNumber) return '/onboarding/profile';
  if (!user.defaultAddressId) return '/onboarding/address';
  return '/account';
}
