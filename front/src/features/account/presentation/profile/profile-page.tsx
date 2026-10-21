import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { ArrowLeft, BadgeCheck, LogOut, Mail, MapPin, Phone, UserRound } from 'lucide-react';
import type { Address } from '../../domain/models';
import { useSession } from '@/app/providers/session-provider';
import { useServices } from '@/app/providers/services-provider';
import { useToast } from '@/app/providers/toast-provider';
import { useAction } from '@/shared/hooks/use-action';
import { Button } from '@/shared/ui/button';
import { Dialog } from '@/shared/ui/dialog';
import { FormError } from '@/shared/ui/form-error';
import { AddressCard } from '../components/address-card';

export function ProfilePage() {
  const { user, setUser } = useSession();
  const services = useServices();
  const { showToast } = useToast();
  const loadAction = useAction();
  const logoutAction = useAction();
  const { run: loadAddresses } = loadAction;
  const navigate = useNavigate();
  const [addresses, setAddresses] = useState<Address[] | null>(null);
  const [logoutOpen, setLogoutOpen] = useState(false);

  useEffect(() => {
    void loadAddresses(() => services.account.listAddresses(), setAddresses);
  }, [loadAddresses, services]);

  if (!user) return null;
  const defaultAddress = addresses?.find(item => item.isDefault);
  return <>
    <div className="profile-heading">
      <div className="avatar" aria-hidden="true">{user.name.slice(0, 1)}</div>
      <div><h1 tabIndex={-1}>أهلًا، {user.name.split(' ')[0]}</h1><p>كل تفاصيل حسابك، في مكان واحد.</p></div>
    </div>
    {!user.profileComplete && <div className="completion-note"><MapPin size={20} /><div><strong>خطوة وتبقى جاهز للتوصيل</strong><p>كمّل رقمك وعنوانك عشان حسابك يبقى جاهز.</p></div><Link to={!user.phoneNumber ? '/onboarding/profile' : '/onboarding/address'} aria-label="استكمال بيانات الحساب"><ArrowLeft size={18} /></Link></div>}
    <div className="detail-row"><UserRound size={19} /><div><span>الاسم</span><p>{user.name}</p></div><Link to="/account/edit" className="text-link">تعديل</Link></div>
    <div className="detail-row"><Mail size={19} /><div><span>البريد الإلكتروني</span><p><bdi dir="ltr">{user.email}</bdi></p></div>{user.emailVerified && <span className="verified"><BadgeCheck size={14} />مؤكد</span>}</div>
    <div className="detail-row"><Phone size={19} /><div><span>رقم الموبايل</span><p><bdi dir="ltr">{user.phoneNumber || 'لسه مضافش'}</bdi></p></div>{!user.phoneNumber && <Link to="/account/edit" className="text-link">إضافة</Link>}</div>
    <div className="section-heading"><h2>عنوان التوصيل</h2><Link className="text-link" to="/account/addresses">إدارة العناوين</Link></div>
    <FormError message={loadAction.error} />
    {loadAction.error && <Button variant="secondary" loading={loadAction.pending} onClick={() => void loadAddresses(() => services.account.listAddresses(), setAddresses)}>إعادة تحميل العنوان</Button>}
    {defaultAddress ? <AddressCard address={defaultAddress} compact />
      : addresses ? <Link to="/account/addresses/new" className="empty-state empty-link"><MapPin size={26} /><p>ضيف عنوان عشان توصيل أسهل.</p><span className="text-link">إضافة عنوان جديد</span></Link>
        : !loadAction.error && <p role="status" className="caption">جاري تحميل العنوان…</p>}
    <button type="button" className="logout-button" onClick={() => { logoutAction.clearError(); setLogoutOpen(true); }}><LogOut size={17} />تسجيل الخروج</button>
    <Dialog open={logoutOpen} title="تسجيل الخروج؟" onClose={() => { if (!logoutAction.pending) setLogoutOpen(false); }}>
      <p>تقدر ترجع في أي وقت. بيانات حسابك هتفضل محفوظة بأمان.</p>
      <FormError message={logoutAction.error} />
      <div className="dialog-actions">
        <Button variant="secondary" disabled={logoutAction.pending} onClick={() => setLogoutOpen(false)}>أفضل في حسابي</Button>
        <Button loading={logoutAction.pending} onClick={() => void logoutAction.run(() => services.auth.signOut(), () => {
          setUser(null);
          showToast('تم تسجيل الخروج.');
          navigate('/login', { replace: true });
        })}>تسجيل الخروج</Button>
      </div>
    </Dialog>
  </>;
}
