import { AppError } from '../../../shared/domain/app-error';

export function normalizeEmail(value: string): string {
  const email = value.trim().toLowerCase();
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new AppError('validation_error', 'راجع البريد الإلكتروني.', { email: 'اكتب بريد إلكتروني صحيح.' });
  }
  return email;
}

export function normalizeName(value: string): string {
  const name = value.trim().replace(/\s+/g, ' ');
  if (name.length < 1 || name.length > 100) {
    throw new AppError('validation_error', 'راجع الاسم.', { name: 'الاسم مطلوب، بحد أقصى 100 حرف.' });
  }
  return name;
}

export function validatePassword(password: string, isNew: boolean): string {
  const minimum = isNew ? 15 : 1;
  if (!password.trim() || password.length < minimum || password.length > 128) {
    const message = isNew ? 'استخدم من 15 إلى 128 حرف. جملة سهلة التذكر اختيار مناسب.' : 'اكتب كلمة المرور، بحد أقصى 128 حرف.';
    throw new AppError('validation_error', 'راجع كلمة المرور.', { password: message });
  }
  return password;
}

export function requireToken(token: string): string {
  if (!token.trim()) throw new AppError('invalid_token', 'الرابط غير صالح. اطلب رابط جديد.');
  return token.trim();
}
