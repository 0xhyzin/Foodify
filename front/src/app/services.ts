import { createSignIn } from "../features/auth/application/sign-in/use-case";
import { createSignUp } from "../features/auth/application/sign-up/use-case";
import { createConfirmEmail } from "../features/auth/application/confirm-email/use-case";
import { createResendVerification } from "../features/auth/application/resend-verification/use-case";
import { createRequestPasswordReset } from "../features/auth/application/request-password-reset/use-case";
import { createResetPassword } from "../features/auth/application/reset-password/use-case";
import { createSignInWithProvider } from "../features/auth/application/sign-in-with-provider/use-case";
import { createSignOut } from "../features/auth/application/sign-out/use-case";
import { createGetSession } from "../features/auth/application/get-session/use-case";
import { createGetProfile } from "../features/account/application/get-profile/use-case";
import { createUpdateProfile } from "../features/account/application/update-profile/use-case";
import { createListAddresses } from "../features/account/application/list-addresses/use-case";
import { createSaveAddress } from "../features/account/application/save-address/use-case";
import { createRemoveAddress } from "../features/account/application/remove-address/use-case";
import { createMakeAddressDefault } from "../features/account/application/make-address-default/use-case";
import type { AccountRepository } from "../features/account/domain/account-repository";
import type { AuthRepository } from "../features/auth/domain/auth-repository";
import { appConfig } from "./config";
import { FetchHttpClient } from "../infrastructure/http/fetch-client";
import { BrowserSessionManager } from "../infrastructure/http/browser-session";
import { HttpAuthRepository } from "../features/auth/infrastructure/http-auth-repository";
import { HttpAccountRepository } from "../features/account/infrastructure/http-account-repository";
import { BrowserOAuthFlow } from "../features/auth/infrastructure/oauth-flow";
import type { MarketplaceServices } from "../features/marketplace/application/services";
import {
  createHttpMarketplace,
} from "../features/marketplace/infrastructure/composition";

export interface DemoControls {
  getVerificationToken(email: string): string | null;
  getResetToken(email: string): string | null;
  reset(): void;
}

export interface AppServices {
  marketplace: MarketplaceServices;
  auth: AuthRepository;
  account: AccountRepository;
  demo: DemoControls;
}

/** The composition root is the only place that selects concrete data adapters. */
export function createAppServices(): AppServices {
  return createApiServices();
}

function createApiServices(): AppServices {
  const session = new BrowserSessionManager(appConfig.apiBaseUrl);
  const client = new FetchHttpClient(appConfig.apiBaseUrl, session);
  const oauth = new BrowserOAuthFlow(client, (current) =>
    session.accept(current),
  );
  const authRepository = new HttpAuthRepository(client, session, oauth);
  const accountRepository = new HttpAccountRepository(client);

  return {
    marketplace: createHttpMarketplace(client),
    auth: {
      signIn: createSignIn(authRepository),
      signUp: createSignUp(authRepository),
      confirmEmail: createConfirmEmail(authRepository),
      resendVerification: createResendVerification(authRepository),
      requestPasswordReset: createRequestPasswordReset(authRepository),
      resetPassword: createResetPassword(authRepository),
      signInWithProvider: createSignInWithProvider(authRepository),
      completeProviderSignIn: (input) =>
        authRepository.completeProviderSignIn(input),
      cancelProviderSignIn: () => authRepository.cancelProviderSignIn(),
      onSessionInvalidated: (listener) =>
        authRepository.onSessionInvalidated(listener),
      signOut: createSignOut(authRepository),
      getSession: createGetSession(authRepository),
    },
    account: {
      getProfile: createGetProfile(accountRepository),
      updateProfile: createUpdateProfile(accountRepository),
      listAddresses: createListAddresses(accountRepository),
      saveAddress: createSaveAddress(accountRepository),
      removeAddress: createRemoveAddress(accountRepository),
      makeAddressDefault: createMakeAddressDefault(accountRepository),
    },
    demo: {
      getVerificationToken: () => null,
      getResetToken: () => null,
      reset: () => undefined,
    },
  };
}
