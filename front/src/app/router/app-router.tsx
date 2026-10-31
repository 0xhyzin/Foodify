import { lazy, Suspense } from "react";
import { LoadingState } from "@/shared/ui/loading-state";
import { MarketplaceProvider } from "@/features/marketplace/presentation/marketplace-provider";
import { MarketplaceLayout } from "@/features/marketplace/presentation/marketplace-layout";
import { MarketplacePage } from "@/features/marketplace/presentation/pages/marketplace-page";
import { MerchantPage } from "@/features/marketplace/presentation/pages/merchant-page";
import { CartsPage } from "@/features/marketplace/presentation/pages/carts-page";
import { HashRouter, Route, Routes } from "react-router";
import { AccountLayout } from "@/app/layouts/account-layout";
import { SessionProvider } from "@/app/providers/session-provider";
import {
  GuestOnly,
  RequireCompleteProfile,
  RequirePhone,
  RequireSession,
} from "./route-guards";
import { RouteEffects } from "./route-effects";
import { NotFoundPage } from "./not-found-page";
import {
  LoginPage,
  RegisterPage,
  VerifyEmailPage,
  ConfirmEmailPage,
  ForgotPasswordPage,
  ResetPasswordSentPage,
  ResetPasswordPage,
  ResetPasswordSuccessPage,
  SocialSignInPage,
  OAuthCallbackPage,
} from "@/features/auth/presentation";
import { CompleteProfilePage } from "@/features/account/presentation/onboarding/complete-profile-page";
import { CompleteAddressPage } from "@/features/account/presentation/onboarding/complete-address-page";
import { AccountReadyPage } from "@/features/account/presentation/onboarding/account-ready-page";
import { ProfilePage } from "@/features/account/presentation/profile/profile-page";
import { EditProfilePage } from "@/features/account/presentation/profile/edit-profile-page";
import { AddressesPage } from "@/features/account/presentation/addresses/addresses-page";
import { AddressEditorPage } from "@/features/account/presentation/addresses/address-editor-page";
const CheckoutPage = lazy(() =>
  import("@/features/marketplace/presentation/pages/checkout-page").then(
    (m) => ({ default: m.CheckoutPage }),
  ),
);
const OrdersPage = lazy(() =>
  import("@/features/marketplace/presentation/pages/orders-page").then((m) => ({
    default: m.OrdersPage,
  })),
);
const OrderPage = lazy(() =>
  import("@/features/marketplace/presentation/pages/order-page").then((m) => ({
    default: m.OrderPage,
  })),
);
const OperationsPage = lazy(() =>
  import("@/features/marketplace/presentation/pages/operations-page").then(
    (m) => ({ default: m.OperationsPage }),
  ),
);
export function AppRouter() {
  return (
    <HashRouter>
      <SessionProvider>
        <MarketplaceProvider>
          <RouteEffects />
          <Suspense fallback={<LoadingState />}>
            <Routes>
              <Route element={<MarketplaceLayout />}>
                <Route index element={<MarketplacePage />} />
                <Route
                  path="restaurants/:restaurantId"
                  element={<MerchantPage />}
                />
                <Route element={<RequireSession />}>
                  <Route path="carts" element={<CartsPage />} />
                  <Route path="orders" element={<OrdersPage />} />
                  <Route path="orders/:orderId" element={<OrderPage />} />
                  <Route path="operations" element={<OperationsPage />} />
                  <Route element={<RequireCompleteProfile />}>
                    <Route
                      path="checkout/:restaurantId"
                      element={<CheckoutPage />}
                    />
                  </Route>
                </Route>
                <Route
                  path="*"
                  element={
                    <div className="catalog-missing-page">
                      <NotFoundPage />
                    </div>
                  }
                />
              </Route>
              <Route element={<AccountLayout />}>
                <Route path="oauth/callback" element={<OAuthCallbackPage />} />
                <Route element={<GuestOnly />}>
                  <Route path="login" element={<LoginPage />} />
                  <Route path="register" element={<RegisterPage />} />
                  <Route
                    path="oauth/:provider"
                    element={<SocialSignInPage />}
                  />
                </Route>
                <Route path="verify-email" element={<VerifyEmailPage />} />
                <Route
                  path="verify-email/confirm"
                  element={<ConfirmEmailPage />}
                />
                <Route
                  path="forgot-password"
                  element={<ForgotPasswordPage />}
                />
                <Route
                  path="reset-password/sent"
                  element={<ResetPasswordSentPage />}
                />
                <Route path="reset-password" element={<ResetPasswordPage />} />
                <Route
                  path="reset-password/success"
                  element={<ResetPasswordSuccessPage />}
                />
                <Route element={<RequireSession />}>
                  <Route
                    path="onboarding/profile"
                    element={<CompleteProfilePage />}
                  />
                  <Route element={<RequirePhone />}>
                    <Route
                      path="onboarding/address"
                      element={<CompleteAddressPage />}
                    />
                  </Route>
                  <Route element={<RequireCompleteProfile />}>
                    <Route
                      path="onboarding/complete"
                      element={<AccountReadyPage />}
                    />
                  </Route>
                  <Route path="account" element={<ProfilePage />} />
                  <Route path="account/edit" element={<EditProfilePage />} />
                  <Route path="account/addresses" element={<AddressesPage />} />
                  <Route
                    path="account/addresses/new"
                    element={<AddressEditorPage />}
                  />
                  <Route
                    path="account/addresses/:id/edit"
                    element={<AddressEditorPage />}
                  />
                </Route>
              </Route>
            </Routes>
          </Suspense>
        </MarketplaceProvider>
      </SessionProvider>
    </HashRouter>
  );
}
