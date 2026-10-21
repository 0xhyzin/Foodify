export interface SignInRequestDto {
  email: string;
  password: string;
}

export interface SignUpRequestDto extends SignInRequestDto {
  name: string;
}

export interface EmailRequestDto {
  email: string;
}

export interface ConfirmEmailRequestDto {
  token: string;
}

export interface ResetPasswordRequestDto extends ConfirmEmailRequestDto {
  password: string;
}

export interface MessageResponseDto {
  message: string;
}
