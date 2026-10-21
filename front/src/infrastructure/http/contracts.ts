export interface BackendUserDto {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  email_verified: boolean;
  roles: string[];
  permissions: string[];
  profile_complete: boolean;
  default_address_id: string | null;
  created_at: string;
}
export interface BrowserSessionDto {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: BackendUserDto;
}
export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown;
  authenticated?: boolean;
  signal?: AbortSignal;
}
export interface HttpClient {
  request<T>(path: string, options?: RequestOptions): Promise<T>;
}
export interface BrowserSessionPort {
  accept(session: BrowserSessionDto): void;
  restore(force?: boolean): Promise<BrowserSessionDto | null>;
  current(): BrowserSessionDto | null;
  clear(): void;
  signOut(): Promise<void>;
  subscribe(listener: () => void): () => void;
}
