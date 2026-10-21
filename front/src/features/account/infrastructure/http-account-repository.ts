import type { BackendUserDto, HttpClient } from '../../../infrastructure/http/contracts';
import { AppError } from '../../../shared/domain/app-error';
import type { AccountRepository, UpdateProfileInput } from '../domain/account-repository';
import type { Address, AddressInput, UserProfile } from '../domain/models';
import type { AddressCoordinatesDto, AddressResponseDto, UpdateProfileDto } from './dto/account-dto';
import { toAddress, toAddressWriteDto } from './mappers/address-mapper';
import { toUserProfile } from './mappers/user-profile-mapper';

export class HttpAccountRepository implements AccountRepository {
  private readonly coordinates = new Map<string, AddressCoordinatesDto>();

  constructor(private readonly client: HttpClient) {}

  async getProfile(): Promise<UserProfile> {
    return toUserProfile(await this.client.request<BackendUserDto>('/users/me'));
  }

  async updateProfile(input: UpdateProfileInput): Promise<UserProfile> {
    const body: UpdateProfileDto = { name: input.name, phone: input.phoneNumber };
    return toUserProfile(await this.client.request<BackendUserDto>('/users/me', { method: 'PATCH', body }));
  }

  async listAddresses(): Promise<Address[]> {
    const response = await this.client.request<AddressResponseDto[]>('/users/me/addresses');
    if (!Array.isArray(response)) {
      throw new AppError('invalid_response', 'استجابة قائمة العناوين غير مكتملة. جرّب مرة تانية.');
    }
    const addresses = response.map(toAddress);
    this.coordinates.clear();
    response.forEach(dto => this.rememberCoordinates(dto));
    return addresses;
  }

  async saveAddress(input: AddressInput, id?: string): Promise<Address> {
    // PUT replaces the whole address. Retain saved coordinates absent from the form.
    if (id && !this.coordinates.has(id)) await this.listAddresses();
    const path = id ? `/users/me/addresses/${encodeURIComponent(id)}` : '/users/me/addresses';
    const dto = await this.client.request<AddressResponseDto>(path, {
      method: id ? 'PUT' : 'POST',
      body: toAddressWriteDto(input, id ? this.coordinates.get(id) : undefined),
    });
    const address = toAddress(dto);
    this.rememberCoordinates(dto);
    return address;
  }

  async removeAddress(id: string): Promise<void> {
    await this.client.request<void>(`/users/me/addresses/${encodeURIComponent(id)}`, { method: 'DELETE' });
    this.coordinates.delete(id);
  }

  async makeAddressDefault(id: string): Promise<void> {
    await this.client.request<BackendUserDto>(`/users/me/default-address/${encodeURIComponent(id)}`, { method: 'PUT' });
  }

  private rememberCoordinates(dto: AddressResponseDto): void {
    this.coordinates.set(dto.id, { latitude: dto.latitude, longitude: dto.longitude });
  }
}
