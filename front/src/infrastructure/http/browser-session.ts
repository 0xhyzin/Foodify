import { AppError } from '../../shared/domain/app-error';
import type { BrowserSessionDto, BrowserSessionPort } from './contracts';
import { readApiError, readJson } from './api-error';
import { parseBrowserSession } from './session-dto';

const clientHeader = { 'X-Foodify-Client': 'web', Accept: 'application/json' };

export class BrowserSessionManager implements BrowserSessionPort {
  private session: BrowserSessionDto | null = null;
  private refreshPromise: Promise<BrowserSessionDto | null> | null = null;
  private logoutPromise: Promise<void> | null = null;
  private revision = 0;
  private restoreBlocked = false;
  private readonly listeners = new Set<() => void>();

  constructor(private readonly baseUrl: string) {}

  accept(value: BrowserSessionDto): void {
    const session = parseBrowserSession(value);
    this.revision += 1;
    this.restoreBlocked = false;
    this.session = session;
    this.notify();
  }

  async restore(force = false): Promise<BrowserSessionDto | null> {
    if (this.restoreBlocked) return null;
    if (!force && this.session) return this.session;
    if (this.refreshPromise) return this.refreshPromise;
    const request = this.refreshFromCookie(this.revision);
    this.refreshPromise = request;
    try {
      return await request;
    } finally {
      if (this.refreshPromise === request) this.refreshPromise = null;
    }
  }

  current(): BrowserSessionDto | null {
    return this.session;
  }

  clear(): void {
    this.revision += 1;
    this.restoreBlocked = true;
    this.session = null;
    this.notify();
  }

  async signOut(): Promise<void> {
    if (this.logoutPromise) return this.logoutPromise;
    const request = this.logoutFromCookie();
    this.logoutPromise = request;
    try {
      await request;
    } finally {
      if (this.logoutPromise === request) this.logoutPromise = null;
    }
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  }

  private async requestSession(path: string): Promise<Response> {
    try {
      return await fetch(this.baseUrl + '/auth/browser/' + path, {
        method: 'POST',
        credentials: 'include',
        headers: clientHeader,
      });
    } catch {
      throw new AppError('network_error', 'مش قادرين نوصل للخدمة دلوقتي. تأكد من الاتصال وحاول تاني.');
    }
  }

  private async logoutFromCookie(): Promise<void> {
    const pendingRefresh = this.refreshPromise;
    const startedAt = ++this.revision;
    this.restoreBlocked = true;
    try {
      // Let an existing rotation finish before clearing its cookie on the server.
      await pendingRefresh?.catch(() => undefined);
      const response = await this.requestSession('logout');
      if (!response.ok && response.status !== 401) throw await readApiError(response);
      if (startedAt === this.revision) this.clear();
    } catch (error) {
      if (startedAt === this.revision) this.restoreBlocked = false;
      throw error;
    }
  }

  private async refreshFromCookie(startedAt: number): Promise<BrowserSessionDto | null> {
    const response = await this.requestSession('refresh');
    // A late response must never restore a session after logout or overwrite login.
    if (startedAt !== this.revision || this.restoreBlocked) return this.session;
    if (response.status === 401) {
      this.clear();
      return null;
    }
    if (!response.ok) throw await readApiError(response);
    const session = parseBrowserSession(await readJson<unknown>(response));
    if (startedAt !== this.revision || this.restoreBlocked) return this.session;
    this.accept(session);
    return this.session;
  }

  private notify(): void {
    this.listeners.forEach(listener => listener());
  }
}
