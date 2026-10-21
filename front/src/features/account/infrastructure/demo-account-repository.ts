import { DemoStore, simulateLatency } from '../../../infrastructure/demo/demo-store';
import { AppError } from '../../../shared/domain/app-error';
import type { AccountRepository, UpdateProfileInput } from '../domain/account-repository';
import type { Address, AddressInput, UserProfile } from '../domain/models';

export class DemoAccountRepository implements AccountRepository {
  constructor(private readonly store: DemoStore) {}

  async getProfile(): Promise<UserProfile> {
    await simulateLatency(120);
    return this.store.toProfile(this.store.currentAccount());
  }

  async updateProfile(input: UpdateProfileInput): Promise<UserProfile> {
    await simulateLatency();
    const account = this.store.currentAccount();
    account.name = input.name;
    account.phoneNumber = input.phoneNumber;
    return this.store.toProfile(account);
  }

  async listAddresses(): Promise<Address[]> {
    await simulateLatency(120);
    const account = this.store.currentAccount();
    return account.addresses.map(address => ({ ...address }));
  }

  async saveAddress(input: AddressInput, id?: string): Promise<Address> {
    await simulateLatency();
    const account = this.store.currentAccount();
    const existing = id ? account.addresses.find(address => address.id === id) : undefined;
    if (id && !existing) throw new AppError('address_not_found', 'العنوان مش موجود.');
    if (!existing && account.addresses.length >= 20) {
      throw new AppError('address_limit_reached', 'تقدر تحفظ لحد 20 عنوان. امسح عنوان قديم عشان تضيف عنوان جديد.');
    }
    const address: Address = {
      ...input, id: existing?.id ?? crypto.randomUUID(),
      floor: input.floor ?? null, apartment: input.apartment ?? null,
      deliveryInstructions: input.deliveryInstructions ?? null,
      isDefault: existing ? existing.id === account.defaultAddressId : account.addresses.length === 0,
    };
    if (existing) account.addresses = account.addresses.map(item => item.id === address.id ? address : item);
    else account.addresses.push(address);
    if (address.isDefault) account.defaultAddressId = address.id;
    return { ...address };
  }

  async removeAddress(id: string): Promise<void> {
    await simulateLatency();
    const account = this.store.currentAccount();
    if (!account.addresses.some(address => address.id === id)) {
      throw new AppError('address_not_found', 'العنوان مش موجود.');
    }
    account.addresses = account.addresses.filter(address => address.id !== id);
    if (account.defaultAddressId === id) account.defaultAddressId = account.addresses[0]?.id ?? null;
    account.addresses = account.addresses.map(address => ({ ...address, isDefault: address.id === account.defaultAddressId }));
  }

  async makeAddressDefault(id: string): Promise<void> {
    await simulateLatency();
    const account = this.store.currentAccount();
    if (!account.addresses.some(address => address.id === id)) {
      throw new AppError('address_not_found', 'العنوان مش موجود.');
    }
    account.defaultAddressId = id;
    account.addresses = account.addresses.map(address => ({ ...address, isDefault: address.id === id }));
  }
}
