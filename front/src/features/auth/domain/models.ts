export type OAuthProvider = 'google' | 'facebook';

export interface SignInInput {
  email: string;
  password: string;
}

export interface SignUpInput {
  name: string;
  email: string;
  password: string;
}

export interface EmailInput {
  email: string;
}

export interface TokenInput {
  token: string;
}

export interface ResetPasswordInput extends TokenInput {
  password: string;
}

export interface CompleteProviderSignInInput {
  ticket: string;
}
