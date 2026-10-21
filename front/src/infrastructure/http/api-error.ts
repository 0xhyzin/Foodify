import { AppError } from '../../shared/domain/app-error';

interface ErrorEnvelope {
  error?: {
    code?: unknown;
    details?: unknown;
    request_id?: unknown;
  };
}

const fieldAliases: Record<string, string> = {
  phone: 'phoneNumber',
  recipient_name: 'recipientName',
  country_code: 'countryCode',
  delivery_notes: 'deliveryInstructions',
  is_default: 'isDefault',
  default_address_id: 'defaultAddressId',
};

const messages: Record<string, string> = {
  invalid_credentials: 'البريد أو كلمة المرور غير صحيحة.',
  email_verification_required: 'أكد بريدك الإلكتروني الأول، وبعدها سجّل الدخول بنفس الطريقة.',
  authentication_required: 'سجّل الدخول عشان تكمل.',
  invalid_token: 'جلسة الدخول انتهت. سجّل الدخول من جديد.',
  invalid_session: 'جلسة الدخول انتهت. سجّل الدخول من جديد.',
  invalid_action_token: 'الرابط غير صالح أو انتهت صلاحيته. اطلب رابط جديد.',
  validation_error: 'راجع البيانات الموضحة وجرب تاني.',
  address_not_found: 'العنوان مش موجود. ارجع لقائمة العناوين.',
  address_limit_reached: 'تقدر تحفظ لحد 20 عنوان. احذف عنوان قديم عشان تضيف غيره.',
  oauth_unavailable: 'تسجيل الدخول بالطريقة دي غير متاح حاليًا.',
  oauth_failed: 'تسجيل الدخول ما اكتملش. ابدأ من جديد.',
  oauth_cancelled: 'تم إلغاء تسجيل الدخول من مزود الخدمة.',
  oauth_email_required: 'مزود الخدمة لم يرجع بريدًا صالحًا. استخدم التسجيل بالبريد.',
  oauth_account_link_required: 'البريد ده مرتبط بحساب موجود. استخدم طريقة دخوله الأصلية.',
  invalid_oauth_state: 'جلسة تسجيل الدخول انتهت. ابدأ من جديد.',
  invalid_oauth_ticket: 'جلسة تسجيل الدخول انتهت أو بدأت من متصفح تاني. ابدأ من جديد.',
  browser_request_rejected: 'تعذر إكمال طلب تسجيل الدخول. افتح رابط الموقع الصحيح وحاول تاني.',
  permission_denied: 'حسابك لا يملك صلاحية لتنفيذ الطلب ده.',
};

function fieldName(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const normalized = value.replace(/^(body|query|path)\./, '');
  if (!normalized || !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(normalized)) return null;
  return Object.hasOwn(fieldAliases, normalized) ? fieldAliases[normalized] : normalized;
}

function fieldsFromDetails(details: unknown): Record<string, string> | undefined {
  if (!Array.isArray(details)) return undefined;
  const fields: Record<string, string> = Object.create(null) as Record<string, string>;
  for (const detail of details) {
    if (!detail || typeof detail !== 'object') continue;
    const item = detail as { field?: unknown; type?: unknown };
    const field = fieldName(item.field);
    if (field) fields[field] = item.type === 'missing' ? 'الحقل ده مطلوب.' : 'راجع قيمة الحقل ده.';
  }
  return Object.keys(fields).length ? fields : undefined;
}

function retryAfterSeconds(value: string | null): number | undefined {
  if (!value) return undefined;
  const seconds = /^\d+$/.test(value)
    ? Number(value)
    : Math.ceil((Date.parse(value) - Date.now()) / 1000);
  return Number.isFinite(seconds) && seconds >= 0 ? Math.min(seconds, 86400) : undefined;
}

export async function readApiError(response: Response): Promise<AppError> {
  let payload: ErrorEnvelope | null = null;
  try {
    payload = await response.clone().json() as ErrorEnvelope;
  } catch {
    // A proxy can return a non-JSON response. Never display its raw body.
  }
  const code = typeof payload?.error?.code === 'string' ? payload.error.code : 'http_' + response.status;
  const retryAfter = retryAfterSeconds(response.headers.get('Retry-After'));
  const message = response.status === 429
    ? 'طلبات كتير في وقت قصير. ' + (retryAfter ? 'حاول بعد ' + retryAfter + ' ثانية.' : 'استنى شوية وحاول تاني.')
    : Object.hasOwn(messages, code)
      ? messages[code]
      : response.status >= 500
        ? 'الخدمة غير متاحة مؤقتًا. جرّب مرة تانية.'
        : 'الطلب ما اكتملش. راجع البيانات وحاول تاني.';
  const requestId = response.headers.get('X-Request-ID') ?? payload?.error?.request_id;
  return new AppError(code, message, fieldsFromDetails(payload?.error?.details), response.status, {
    requestId: typeof requestId === 'string' ? requestId.slice(0, 128) : undefined,
    retryAfterSeconds: retryAfter,
  });
}

export async function readJson<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  try {
    return await response.json() as T;
  } catch {
    throw new AppError('invalid_response', 'استجابة الخادم غير مكتملة. جرّب مرة تانية.', undefined, response.status);
  }
}
