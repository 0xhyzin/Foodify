import type { Address, AddressInput, UserProfile } from './models';

export interface UpdateProfileInput {
  name: string;
  phoneNumber: string;
}

export interface AccountRepository {
  getProfile(): Promise<UserProfile>;
  updateProfile(input: UpdateProfileInput): Promise<UserProfile>;
  listAddresses(): Promise<Address[]>;
  saveAddress(input: AddressInput, id?: string): Promise<Address>;
  removeAddress(id: string): Promise<void>;
  makeAddressDefault(id: string): Promise<void>;
}
