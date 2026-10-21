import { useState, type FormEvent } from 'react';
import { ArrowLeft, Check } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { Field } from '@/shared/ui/field';
import { FormError } from '@/shared/ui/form-error';
import { useAction } from '@/shared/hooks/use-action';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import type { UserProfile } from '../../domain/models';
export function ProfileForm({ user, onboarding, onSaved }: { user: UserProfile; onboarding?: boolean; onSaved(user: UserProfile): void }) {
  const services = useServices();
  const { setUser } = useSession();
  const { run, pending, error, fieldErrors } = useAction();
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phoneNumber?.replace(/^\+20/, '') || '');
  function submit(event: FormEvent) {
    event.preventDefault();
    void run(() => services.account.updateProfile({ name, phoneNumber: phone }), (profile) => { setUser(profile); onSaved(profile); });
  }
  return <form className="form" onSubmit={submit} noValidate aria-busy={pending}>
    <FormError message={error} />
    <Field name="name" label="الاسم" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" maxLength={100} placeholder="اسمك بالكامل" error={fieldErrors.name} required />
    <Field name="phoneNumber" label="رقم الموبايل" type="tel" dir="ltr" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel-national" inputMode="tel" maxLength={16} placeholder="10 1234 5678" hint="رقم مصري يبدأ بـ 01 أو 1. هنحفظه بكود الدولة ‎+20." error={fieldErrors.phoneNumber} required />
    <Button type="submit" loading={pending} icon={onboarding ? <ArrowLeft size={18} /> : <Check size={18} />}>{onboarding ? 'متابعة لعنوان التوصيل' : 'حفظ التغييرات'}</Button>
  </form>;
}
