export interface ApplicationError {
  code: string;
  message: string;
  fields?: Record<string, string>;
  status?: number;
  requestId?: string;
  retryAfterSeconds?: number;
}

export interface ErrorMetadata {
  requestId?: string;
  retryAfterSeconds?: number;
}

export class AppError extends Error implements ApplicationError {
  readonly code: string;
  readonly fields?: Record<string, string>;
  readonly status?: number;
  readonly requestId?: string;
  readonly retryAfterSeconds?: number;

  constructor(code: string, message: string, fields?: Record<string, string>, status?: number, metadata: ErrorMetadata = {}) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.fields = fields;
    this.status = status;
    this.requestId = metadata.requestId;
    this.retryAfterSeconds = metadata.retryAfterSeconds;
  }
}

export function getErrorMessage(error: unknown): string {
  return error instanceof AppError ? error.message : 'حصلت مشكلة غير متوقعة. جرّب مرة تانية.';
}
