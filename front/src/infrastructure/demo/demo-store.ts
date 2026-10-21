import { AppError } from '../../shared/domain/app-error';
import type { Address, UserProfile } from '../../features/account/domain/models';

export interface DemoAccount {
  id: string;
  name: string;
  email: string;
  phoneNumber: string | null;
  emailVerified: boolean;
  defaultAddressId: string | null;
  roles: string[];
  addresses: Address[];
}

interface DemoToken {
  token: string;
  userId: string;
  expiresAt: number;
}

export type DemoTokenPurpose = 'verification' | 'reset';

export class DemoStore {
  readonly accounts = new Map<string, DemoAccount>();
  private readonly verificationTokens = new Map<string, DemoToken>();
  private readonly resetTokens = new Map<string, DemoToken>();
  activeUserId: string | null = null;

  constructor() {
    this.reset();
  }

  reset(): void {
    this.accounts.clear();
    this.verificationTokens.clear();
    this.resetTokens.clear();
    this.activeUserId = null;
    this.accounts.set('demo-mariam', {
      id: 'demo-mariam', name: 'مريم أحمد', email: 'mariam@example.com',
      phoneNumber: '+201012345678', emailVerified: true,
      defaultAddressId: 'demo-home', roles: ['customer'],
      addresses: [{
        id: 'demo-home', label: 'البيت', recipientName: 'مريم أحمد',
        phoneNumber: '+201012345678', countryCode: 'EG', city: 'القاهرة',
        area: 'مدينة نصر', street: 'شارع عباس العقاد', building: '24',
        floor: '3', apartment: '12', deliveryInstructions: 'بجوار الصيدلية، الجرس باسم أحمد.', isDefault: true,
      }],
    });
  }

  findByEmail(email: string): DemoAccount | undefined {
    return [...this.accounts.values()].find(account => account.email === email.trim().toLowerCase());
  }

  currentAccount(): DemoAccount {
    const account = this.activeUserId ? this.accounts.get(this.activeUserId) : undefined;
    if (!account) throw new AppError('authentication_required', 'سجّل الدخول عشان تكمل.');
    return account;
  }

  toProfile(account: DemoAccount): UserProfile {
    return {
      id: account.id, name: account.name, email: account.email,
      phoneNumber: account.phoneNumber, emailVerified: account.emailVerified,
      profileComplete: Boolean(account.phoneNumber && account.defaultAddressId),
      defaultAddressId: account.defaultAddressId, roles: [...account.roles],
    };
  }

  issueToken(email: string, purpose: DemoTokenPurpose): void {
    const account = this.findByEmail(email);
    if (!account) return;
    const tokens = purpose === 'verification' ? this.verificationTokens : this.resetTokens;
    tokens.set(account.email, {
      token: `demo-${purpose}-${crypto.randomUUID()}`, userId: account.id,
      expiresAt: Date.now() + 15 * 60 * 1000,
    });
  }

  previewToken(email: string, purpose: DemoTokenPurpose): string | null {
    const tokens = purpose === 'verification' ? this.verificationTokens : this.resetTokens;
    const record = tokens.get(email.trim().toLowerCase());
    return record && record.expiresAt > Date.now() ? record.token : null;
  }

  consumeToken(token: string, purpose: DemoTokenPurpose): DemoAccount {
    const tokens = purpose === 'verification' ? this.verificationTokens : this.resetTokens;
    const entry = [...tokens.entries()].find(([, record]) => record.token === token);
    if (!entry) throw new AppError('invalid_token', 'الرابط غير صالح أو اتستخدم قبل كده. اطلب رابط جديد.');
    const [email, record] = entry;
    tokens.delete(email);
    const account = this.accounts.get(record.userId);
    if (!account || record.expiresAt <= Date.now()) {
      throw new AppError('invalid_token', 'صلاحية الرابط انتهت. اطلب رابط جديد.');
    }
    return account;
  }
}

export function simulateLatency(milliseconds = 320): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}
