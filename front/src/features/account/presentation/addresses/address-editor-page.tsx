import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import type { Address } from '../../domain/models';
import { useServices } from '@/app/providers/services-provider';
import { useToast } from '@/app/providers/toast-provider';
import { useAction } from '@/shared/hooks/use-action';
import { BackLink } from '@/shared/ui/back-link';
import { PageHeading } from '@/shared/ui/page-heading';
import { LoadingState } from '@/shared/ui/loading-state';
import { FormError } from '@/shared/ui/form-error';
import { Button } from '@/shared/ui/button';
import { AddressForm } from '../components/address-form';
export function AddressEditorPage() {
  const { id } = useParams();
  return <AddressEditor key={id || 'new'} id={id} />;
}
function AddressEditor({ id }: { id?: string }) {
  const services = useServices();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [address, setAddress] = useState<Address | null>(null);
  const [loaded, setLoaded] = useState(!id);
  const { run, pending, error } = useAction();
  useEffect(() => { if (id) void run(() => services.account.listAddresses(), (list) => { setAddress(list.find((item) => item.id === id) || null); setLoaded(true); }); }, [id, run, services]);
  return <><BackLink to="/account/addresses">رجوع للعناوين</BackLink><PageHeading title={id ? 'تعديل العنوان' : 'عنوان جديد'} description="تفاصيل واضحة عشان طلبك يوصل بسهولة." /><FormError message={error} />{!loaded ? (pending ? <LoadingState /> : <Button onClick={() => void run(() => services.account.listAddresses(), (list) => { setAddress(list.find((item) => item.id === id) || null); setLoaded(true); })}>إعادة المحاولة</Button>) : id && !address ? <div className="empty-state"><h2>العنوان مش موجود</h2><p>ممكن يكون اتحذف. ارجع للعناوين المحفوظة.</p></div> : <AddressForm key={id || 'new'} address={address || undefined} onSaved={() => { showToast(id ? 'تعديلات العنوان اتحفظت.' : 'العنوان الجديد اتحفظ.'); navigate('/account/addresses'); }} />}</>;
}
