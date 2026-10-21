import { AppError } from '../../../../shared/domain/app-error';
import type { Address, AddressInput } from '../../domain/models';
import type { AddressCoordinatesDto, AddressResponseDto, AddressWriteDto, CoordinateDto } from '../dto/account-dto';

function isNullableText(value: unknown): value is string | null {
  return value === null || typeof value === 'string';
}

function isCoordinate(value: unknown): value is CoordinateDto {
  return value === null || (typeof value === 'number' && Number.isFinite(value))
    || (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value)));
}

export function toAddress(dto: AddressResponseDto): Address {
  if (!dto || typeof dto !== 'object'
    || typeof dto.id !== 'string' || typeof dto.label !== 'string'
    || typeof dto.recipient_name !== 'string' || typeof dto.phone !== 'string'
    || typeof dto.country_code !== 'string' || typeof dto.city !== 'string'
    || typeof dto.area !== 'string' || typeof dto.street !== 'string'
    || typeof dto.building !== 'string' || typeof dto.is_default !== 'boolean'
    || !isNullableText(dto.floor) || !isNullableText(dto.apartment)
    || !isNullableText(dto.delivery_notes)
    || !isCoordinate(dto.latitude) || !isCoordinate(dto.longitude)
    || (dto.latitude === null) !== (dto.longitude === null)) {
    throw new AppError('invalid_response', 'استجابة بيانات العنوان غير مكتملة. جرّب مرة تانية.');
  }

  return {
    id: dto.id,
    label: dto.label,
    recipientName: dto.recipient_name,
    phoneNumber: dto.phone,
    countryCode: dto.country_code,
    city: dto.city,
    area: dto.area,
    street: dto.street,
    building: dto.building,
    floor: dto.floor,
    apartment: dto.apartment,
    deliveryInstructions: dto.delivery_notes,
    isDefault: dto.is_default,
  };
}

function nullableText(value: string | null | undefined): string | null {
  return value?.trim() || null;
}

/** Explicit fields prevent UI metadata from leaking into write requests. */
export function toAddressWriteDto(input: AddressInput, coordinates?: AddressCoordinatesDto): AddressWriteDto {
  return {
    label: input.label,
    recipient_name: input.recipientName,
    phone: input.phoneNumber,
    country_code: input.countryCode,
    city: input.city,
    area: input.area,
    street: input.street,
    building: input.building,
    floor: nullableText(input.floor),
    apartment: nullableText(input.apartment),
    delivery_notes: nullableText(input.deliveryInstructions),
    latitude: coordinates?.latitude ?? null,
    longitude: coordinates?.longitude ?? null,
  };
}
