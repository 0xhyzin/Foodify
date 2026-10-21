import { AppError } from '../../../shared/domain/app-error';
import type { AddressInput } from './models';

function asciiDigits(value: string): string {
  return value.replace(/[٠-٩]/g, digit => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
    .replace(/[۰-۹]/g, digit => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)));
}

export function normalizeEgyptianPhone(value: string, field = 'phoneNumber'): string {
  let phone = asciiDigits(value).replace(/[\s()-]/g, '');
  if (phone.startsWith('0020')) phone = `+20${phone.slice(4)}`;
  if (/^01[0125]\d{8}$/.test(phone)) phone = `+20${phone.slice(1)}`;
  if (/^1[0125]\d{8}$/.test(phone)) phone = `+20${phone}`;
  if (!/^\+201[0125]\d{8}$/.test(phone)) {
    throw new AppError('validation_error', 'راجع رقم الموبايل.', { [field]: 'اكتب رقم موبايل مصري صحيح، مثل 01012345678.' });
  }
  return phone;
}

function requiredText(value: string, field: string, label: string, maximum: number): string {
  const text = value.trim();
  if (!text || text.length > maximum) {
    throw new AppError('validation_error', 'راجع بيانات العنوان.', { [field]: `${label} مطلوب، بحد أقصى ${maximum} حرف.` });
  }
  return text;
}

function optionalText(value: string | null | undefined, field: string, label: string, maximum: number): string | null {
  const text = value?.trim() || null;
  if (text && text.length > maximum) {
    throw new AppError('validation_error', 'راجع بيانات العنوان.', { [field]: `${label} بحد أقصى ${maximum} حرف.` });
  }
  return text;
}

export function normalizeAddress(input: AddressInput): AddressInput {
  const countryCode = input.countryCode.trim().toUpperCase();
  if (!/^[A-Z]{2}$/.test(countryCode)) {
    throw new AppError('validation_error', 'راجع بيانات العنوان.', { countryCode: 'اكتب رمز الدولة من حرفين، مثل EG.' });
  }
  return {
    label: requiredText(input.label, 'label', 'اسم العنوان', 50),
    recipientName: requiredText(input.recipientName, 'recipientName', 'اسم المستلم', 100),
    phoneNumber: normalizeEgyptianPhone(input.phoneNumber),
    countryCode,
    city: requiredText(input.city, 'city', 'المحافظة', 100),
    area: requiredText(input.area, 'area', 'المنطقة', 100),
    street: requiredText(input.street, 'street', 'الشارع', 200),
    building: requiredText(input.building, 'building', 'رقم العمارة', 50),
    floor: optionalText(input.floor, 'floor', 'الدور', 30),
    apartment: optionalText(input.apartment, 'apartment', 'الشقة', 30),
    deliveryInstructions: optionalText(input.deliveryInstructions, 'deliveryInstructions', 'تعليمات التوصيل', 500),
  };
}

export function requireAddressId(id: string): string {
  if (!id.trim()) throw new AppError('address_not_found', 'العنوان مش موجود.');
  return id;
}
