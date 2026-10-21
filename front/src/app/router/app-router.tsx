import { HashRouter, Navigate, Route, Routes } from 'react-router';
import { AccountLayout } from '@/app/layouts/account-layout';
import { GuestOnly, RequireCompleteProfile, RequirePhone, RequireSession } from './route-guards';
import { RouteEffects } from './route-effects';
import { NotFoundPage } from './not-found-page';
import { LoginPage, RegisterPage, VerifyEmailPage, ConfirmEmailPage, ForgotPasswordPage, ResetPasswordSentPage, ResetPasswordPage, ResetPasswordSuccessPage, SocialSignInPage, OAuthCallbackPage } from '@/features/auth/presentation';
import { CompleteProfilePage } from '@/features/account/presentation/onboarding/complete-profile-page';
import { CompleteAddressPage } from '@/features/account/presentation/onboarding/complete-address-page';
import { AccountReadyPage } from '@/features/account/presentation/onboarding/account-ready-page';
import { ProfilePage } from '@/features/account/presentation/profile/profile-page';
import { EditProfilePage } from '@/features/account/presentation/profile/edit-profile-page';
import { AddressesPage } from '@/features/account/presentation/addresses/addresses-page';
import { AddressEditorPage } from '@/features/account/presentation/addresses/address-editor-page';
export function AppRouter() {
  return <HashRouter><RouteEffects /><Routes><Route element={<AccountLayout />}>
    <Route index element={<Navigate to="/login" replace />} />
    <Route path="oauth/callback" element={<OAuthCallbackPage />} />
    <Route element={<GuestOnly />}><Route path="login" element={<LoginPage />} /><Route path="register" element={<RegisterPage />} /><Route path="oauth/:provider" element={<SocialSignInPage />} /></Route>
    <Route path="verify-email" element={<VerifyEmailPage />} /><Route path="verify-email/confirm" element={<ConfirmEmailPage />} />
    <Route path="forgot-password" element={<ForgotPasswordPage />} /><Route path="reset-password/sent" element={<ResetPasswordSentPage />} /><Route path="reset-password" element={<ResetPasswordPage />} /><Route path="reset-password/success" element={<ResetPasswordSuccessPage />} />
    <Route element={<RequireSession />}>
      <Route path="onboarding/profile" element={<CompleteProfilePage />} />
      <Route element={<RequirePhone />}><Route path="onboarding/address" element={<CompleteAddressPage />} /></Route>
      <Route element={<RequireCompleteProfile />}><Route path="onboarding/complete" element={<AccountReadyPage />} /></Route>
      <Route path="account" element={<ProfilePage />} /><Route path="account/edit" element={<EditProfilePage />} /><Route path="account/addresses" element={<AddressesPage />} /><Route path="account/addresses/new" element={<AddressEditorPage />} /><Route path="account/addresses/:id/edit" element={<AddressEditorPage />} />
    </Route><Route path="*" element={<NotFoundPage />} />
  </Route></Routes></HashRouter>;
}
