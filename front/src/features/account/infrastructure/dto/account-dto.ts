/** Wire contracts follow the FastAPI address and profile DTOs. */
export type CoordinateDto = string | number | null;

export interface AddressCoordinatesDto {
  latitude: CoordinateDto;
  longitude: CoordinateDto;
}

export interface AddressWriteDto extends AddressCoordinatesDto {
  label: string;
  recipient_name: string;
  phone: string;
  country_code: string;
  city: string;
  area: string;
  street: string;
  building: string;
  floor: string | null;
  apartment: string | null;
  delivery_notes: string | null;
}

export interface AddressResponseDto extends AddressWriteDto {
  id: string;
  is_default: boolean;
  created_at: string;
}

export interface UpdateProfileDto {
  name: string;
  phone: string;
}
