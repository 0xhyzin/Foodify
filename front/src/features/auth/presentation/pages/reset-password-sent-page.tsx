import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { Mail, MailCheck } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { BackLink } from '@/shared/ui/back-link';
import { Button } from '@/shared/ui/button';
import { StatusView } from '@/shared/ui/status-view';
import { EmailPreview } from '../components/email-preview';
import { appConfig } from '@/app/config';

export function ResetPasswordSentPage() {
  const [params] = useSearchParams();
  const email = params.get('email') ?? '';
  const services = useServices();
  const [inboxOpen, setInboxOpen] = useState(false);

  if (!email) return <StatusView icon={Mail} title="نرجّعلك الوصول لحسابك" description="اكتب بريدك الإلكتروني عشان تطلب رابط تغيير كلمة المرور."><Link className="button button-primary" to="/forgot-password">طلب رابط التغيير</Link></StatusView>;

  return <>
    <BackLink to="/forgot-password">تعديل البريد الإلكتروني</BackLink>
    <StatusView icon={MailCheck} title="راجع بريدك الإلكتروني" description="لو البريد ده مرتبط بحساب، هتلاقي رسالة فيها رابط تغيير كلمة المرور.">
      <div className="email-chip"><Mail size={18} aria-hidden="true" /><bdi>{email}</bdi></div>
      {appConfig.isDemo && <Button onClick={() => setInboxOpen(true)} icon={<Mail size={19} aria-hidden="true" />}>فتح البريد التجريبي</Button>}
      <p className="note">الرابط صالح للاستخدام مرة واحدة. لو انتهت صلاحيته، اطلب رابط جديد.</p>
      <Link className="text-link" to="/forgot-password">طلب رابط جديد</Link>
    </StatusView>
    {appConfig.isDemo && <EmailPreview open={inboxOpen} onClose={() => setInboxOpen(false)} email={email} token={services.demo.getResetToken(email)} kind="reset" />}
  </>;
}
