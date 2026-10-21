export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phoneNumber: string | null;
  emailVerified: boolean;
  profileComplete: boolean;
  defaultAddressId: string | null;
  roles: string[];
}

export interface Address {
  id: string;
  label: string;
  recipientName: string;
  phoneNumber: string;
  countryCode: string;
  city: string;
  area: string;
  street: string;
  building: string;
  floor: string | null;
  apartment: string | null;
  deliveryInstructions: string | null;
  isDefault: boolean;
}

export interface AddressInput {
  label: string;
  recipientName: string;
  phoneNumber: string;
  countryCode: string;
  city: string;
  area: string;
  street: string;
  building: string;
  floor?: string | null;
  apartment?: string | null;
  deliveryInstructions?: string | null;
}
