import { AppError } from "../../shared/domain/app-error";
import type {
  BrowserSessionPort,
  HttpClient,
  RequestOptions,
} from "./contracts";
import { readApiError, readJson } from "./api-error";

const clientHeader = { "X-Foodify-Client": "web", Accept: "application/json" };

export class FetchHttpClient implements HttpClient {
  constructor(
    private readonly baseUrl: string,
    private readonly session: BrowserSessionPort,
  ) {}

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const authenticated = options.authenticated !== false;
    const initialSession = authenticated ? this.session.current() : null;
    const accessToken = initialSession?.access_token;
    const response = await this.send(path, options, accessToken);
    if (response.status === 401 && authenticated) {
      options.signal?.throwIfAborted();
      const current = this.session.current();
      if (
        initialSession &&
        current &&
        initialSession.user.id !== current.user.id
      ) {
        throw new AppError(
          "authentication_required",
          "الحساب اتغير. افتح الصفحة من جديد قبل إعادة الطلب.",
          undefined,
          401,
        );
      }
      // Another request may already have refreshed the token that was rejected.
      const refreshed =
        current && current.access_token !== accessToken
          ? current
          : await this.session.restore(true);
      if (refreshed) {
        if (initialSession && initialSession.user.id !== refreshed.user.id) {
          throw new AppError(
            "authentication_required",
            "الحساب اتغير. افتح الصفحة من جديد قبل إعادة الطلب.",
            undefined,
            401,
          );
        }
        options.signal?.throwIfAborted();
        const retry = await this.send(path, options, refreshed.access_token);
        if (
          retry.status === 401 &&
          this.session.current()?.access_token === refreshed.access_token
        ) {
          this.session.clear();
        }
        if (!retry.ok) throw await readApiError(retry);
        return readJson<T>(retry);
      }
    }
    if (!response.ok) throw await readApiError(response);
    return readJson<T>(response);
  }

  private async send(
    path: string,
    options: RequestOptions,
    accessToken?: string,
  ): Promise<Response> {
    const headers: Record<string, string> = { ...clientHeader };
    if (options.body !== undefined)
      headers["Content-Type"] = "application/json";
    if (accessToken) headers.Authorization = "Bearer " + accessToken;
    if (options.idempotencyKey)
      headers["Idempotency-Key"] = options.idempotencyKey;
    try {
      return await fetch(this.baseUrl + path, {
        method: options.method ?? "GET",
        credentials: "include",
        headers,
        body:
          options.body === undefined ? undefined : JSON.stringify(options.body),
        signal: options.signal,
      });
    } catch (error) {
      if (options.signal?.aborted) throw error;
      throw new AppError(
        "network_error",
        "مش قادرين نوصل للخدمة دلوقتي. تأكد من الاتصال وحاول تاني.",
      );
    }
  }
}
