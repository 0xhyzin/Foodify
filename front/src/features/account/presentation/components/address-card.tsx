import { BriefcaseBusiness, House, MapPin, Pencil, Star, Trash2 } from 'lucide-react';
import { Link } from 'react-router';
import type { Address } from '../../domain/models';
export function AddressCard({ address, compact = false, busy = false, onDelete, onDefault }: { address: Address; compact?: boolean; busy?: boolean; onDelete?(address: Address): void; onDefault?(address: Address): void }) {
  const Icon = address.label === 'الشغل' ? BriefcaseBusiness : address.label === 'البيت' ? House : MapPin;
  return <article className={`address-card ${address.isDefault ? 'is-default' : ''}`} aria-label={address.label}>
    <div className="address-card-top"><h3><Icon size={19} aria-hidden="true" />{address.label}</h3>{address.isDefault && <span className="badge">الافتراضي</span>}</div>
    <p>{address.street}، عمارة {address.building}{address.floor ? `، الدور ${address.floor}` : ''}{address.apartment ? `، شقة ${address.apartment}` : ''}<br />{address.area}، {address.city}</p>
    {!compact && <><p className="address-recipient">{address.recipientName} · <bdi dir="ltr">{address.phoneNumber}</bdi></p>{address.deliveryInstructions && <p className="address-notes">{address.deliveryInstructions}</p>}<div className="address-actions"><Link className="text-link" to={`/account/addresses/${address.id}/edit`} aria-label={`تعديل عنوان ${address.label}`} aria-disabled={busy || undefined} onClick={(e) => { if (busy) e.preventDefault(); }}><Pencil size={14} />تعديل</Link>{!address.isDefault && <button type="button" className="text-link" disabled={busy} onClick={() => onDefault?.(address)}><Star size={14} />تعيين كافتراضي</button>}<button type="button" className="text-link muted" disabled={busy} onClick={() => onDelete?.(address)} aria-label={`حذف عنوان ${address.label}`}><Trash2 size={14} />حذف</button></div></>}
  </article>;
}
