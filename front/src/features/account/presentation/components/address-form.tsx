import { useState, type FormEvent } from 'react';
import { BriefcaseBusiness, Check, House, MapPin, UserRound } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { Field } from '@/shared/ui/field';
import { FormError } from '@/shared/ui/form-error';
import { useAction } from '@/shared/hooks/use-action';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { useToast } from '@/app/providers/toast-provider';
import type { Address, AddressInput } from '../../domain/models';
export function AddressForm({ address, onSaved }: { address?: Address; onSaved(): void }) {
  const services = useServices();
  const { user, refresh, setUser } = useSession();
  const { showToast } = useToast();
  const { run, pending, error, fieldErrors } = useAction();
  const [values, setValues] = useState<AddressInput>(() => ({ label: address?.label || 'البيت', recipientName: address?.recipientName || user?.name || '', phoneNumber: address?.phoneNumber || user?.phoneNumber || '', countryCode: address?.countryCode || 'EG', city: address?.city || '', area: address?.area || '', street: address?.street || '', building: address?.building || '', floor: address?.floor || '', apartment: address?.apartment || '', deliveryInstructions: address?.deliveryInstructions || '' }));
  const [labelType, setLabelType] = useState(() => !address || address.label === 'البيت' || address.label === 'الشغل' ? address?.label || 'البيت' : 'مكان تاني');
  const [recipientOpen, setRecipientOpen] = useState(false);
  const update = (key: keyof AddressInput, value: string) => setValues((current) => ({ ...current, [key]: value }));
  const field = (key: keyof AddressInput, label: string, placeholder: string, maxLength: number, required = true) => <Field name={key} label={label} value={values[key] || ''} onChange={(e) => update(key, e.target.value)} placeholder={placeholder} maxLength={maxLength} error={fieldErrors[key]} required={required} />;
  function submit(event: FormEvent) {
    event.preventDefault();
    void run(() => services.account.saveAddress(values, address?.id), async saved => {
      // The write has succeeded. A failed follow-up read must not invite a duplicate POST.
      if (user && saved.isDefault) {
        setUser({ ...user, defaultAddressId: saved.id, profileComplete: Boolean(user.phoneNumber) });
      }
      let refreshFailed = false;
      try { await refresh(); } catch { refreshFailed = true; }
      onSaved();
      if (refreshFailed) showToast('العنوان اتحفظ، لكن تعذر تحديث باقي بيانات الحساب. حاول تحديث الصفحة بعد شوية.');
    });
  }
  return <form className="form address-form" onSubmit={submit} noValidate aria-busy={pending}>
    <FormError message={error} />
    <div className="recipient-card"><UserRound size={20} aria-hidden="true" /><div><strong>{values.recipientName || 'بيانات المستلم'}</strong><bdi dir="ltr">{values.phoneNumber}</bdi></div><button type="button" className="text-link" onClick={() => setRecipientOpen(!recipientOpen)} aria-expanded={recipientOpen}>تعديل</button></div>
    {(recipientOpen || fieldErrors.recipientName || fieldErrors.phoneNumber) && <div className="form recipient-fields">{field('recipientName', 'اسم المستلم', 'اسم المستلم بالكامل', 100)}<Field name="phoneNumber" label="موبايل المستلم" type="tel" dir="ltr" autoComplete="tel" inputMode="tel" value={values.phoneNumber} onChange={(e) => update('phoneNumber', e.target.value)} error={fieldErrors.phoneNumber} placeholder="+201012345678" maxLength={16} required /></div>}
    <fieldset className="address-labels" disabled={pending}><legend>اسم العنوان</legend><div className="pills">{[{ label: 'البيت', icon: House }, { label: 'الشغل', icon: BriefcaseBusiness }, { label: 'مكان تاني', icon: MapPin }].map(({ label, icon: Icon }) => <button type="button" key={label} className="pill" aria-pressed={labelType === label} onClick={() => { if (labelType === label) return; setLabelType(label); update('label', label === 'مكان تاني' ? '' : label); }}><Icon size={16} />{label}</button>)}</div></fieldset>
    {labelType === 'مكان تاني' && field('label', 'اسم المكان', 'مثال: بيت العيلة', 50)}
    <div className="two-columns">{field('city', 'المدينة', 'مثال: القاهرة', 100)}{field('area', 'المنطقة', 'مثال: مدينة نصر', 100)}</div>
    {field('street', 'الشارع', 'اسم الشارع ورقمه', 200)}
    <div className="two-columns">{field('building', 'رقم العمارة', 'مثال: 24', 50)}{field('floor', 'الدور (اختياري)', 'مثال: 3', 30, false)}</div>
    {field('apartment', 'الشقة (اختياري)', 'مثال: 12', 30, false)}
    <div className="field"><label htmlFor="delivery-instructions">علامة مميزة أو تعليمات (اختياري)</label><textarea id="delivery-instructions" name="deliveryInstructions" maxLength={500} rows={2} value={values.deliveryInstructions || ''} onChange={(e) => update('deliveryInstructions', e.target.value)} placeholder="مثال: بجوار الصيدلية، الجرس باسم أحمد" aria-invalid={!!fieldErrors.deliveryInstructions} aria-describedby={fieldErrors.deliveryInstructions ? 'delivery-error' : undefined} />{fieldErrors.deliveryInstructions && <p className="field-error" id="delivery-error">{fieldErrors.deliveryInstructions}</p>}</div>
    <Button type="submit" loading={pending} icon={<Check size={18} />}>{address ? 'حفظ التعديلات' : 'حفظ عنوان التوصيل'}</Button>
    <p className="caption center">التوصيل داخل مصر. أول عنوان بتحفظه بيبقى الافتراضي.</p>
  </form>;
}
