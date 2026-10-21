import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { MapPin, Plus } from 'lucide-react';
import type { Address } from '../../domain/models';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { useToast } from '@/app/providers/toast-provider';
import { useAction } from '@/shared/hooks/use-action';
import { PageHeading } from '@/shared/ui/page-heading';
import { BackLink } from '@/shared/ui/back-link';
import { Dialog } from '@/shared/ui/dialog';
import { Button } from '@/shared/ui/button';
import { FormError } from '@/shared/ui/form-error';
import { LoadingState } from '@/shared/ui/loading-state';
import { AddressCard } from '../components/address-card';
export function AddressesPage() {
  const services = useServices();
  const { refresh } = useSession();
  const { showToast } = useToast();
  const { run, pending, error } = useAction();
  const [addresses, setAddresses] = useState<Address[] | null>(null);
  const [deleting, setDeleting] = useState<Address | null>(null);
  useEffect(() => { void run(() => services.account.listAddresses(), setAddresses); }, [run, services]);
  async function reload() { setAddresses(await services.account.listAddresses()); await refresh(); }
  return <><BackLink to="/account">رجوع لحسابي</BackLink><PageHeading title="عناويني" description="اختار عنوانك الافتراضي أو ضيف مكان جديد." />
    {!deleting && <FormError message={error} />}
    {!addresses ? (pending ? <LoadingState /> : <Button onClick={() => void run(() => services.account.listAddresses(), setAddresses)}>إعادة المحاولة</Button>) : <>
      {!addresses.length ? <div className="empty-state"><MapPin size={30} /><h2>أول عنوان يبدأ من هنا</h2><p>احفظ عنوانك مرة واحدة عشان توصيل أسهل.</p></div> : <div className="address-list">{addresses.map((address) => <AddressCard key={address.id} address={address} busy={pending} onDelete={setDeleting} onDefault={(item) => void run(() => services.account.makeAddressDefault(item.id), async () => { await reload(); showToast('تم تغيير العنوان الافتراضي.'); })} />)}</div>}
      {addresses.length < 20 ? <Link to="/account/addresses/new" className="button button-primary"><Plus size={18} />إضافة عنوان جديد</Link> : <p className="note">وصلت للحد الأقصى: 20 عنوان. احذف عنوان عشان تضيف غيره.</p>}
    </>}
    <Dialog open={!!deleting} title="تحب تحذف العنوان؟" onClose={() => { if (!pending) setDeleting(null); }}><p>عنوان «{deleting?.label}» هيتشال من حسابك.{deleting?.isDefault && ' لو عندك عنوان تاني هيبقى الافتراضي.'}</p><FormError message={error} /><div className="dialog-actions"><Button variant="secondary" disabled={pending} onClick={() => setDeleting(null)}>رجوع</Button><Button variant="danger" loading={pending} onClick={() => { if (deleting) void run(() => services.account.removeAddress(deleting.id), async () => { setDeleting(null); await reload(); showToast('العنوان اتحذف.'); }); }}>حذف العنوان</Button></div></Dialog>
  </>;
}
