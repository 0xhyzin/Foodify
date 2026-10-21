import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { Info, Mail, MailCheck } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { BackLink } from '@/shared/ui/back-link';
import { Button } from '@/shared/ui/button';
import { StatusView } from '@/shared/ui/status-view';
import { FormError } from '@/shared/ui/form-error';
import { EmailPreview } from '../components/email-preview';
import { useResendVerification } from '../hooks/use-resend-verification';
import { appConfig } from '@/app/config';

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const email = params.get('email') ?? '';
  const services = useServices();
  const [inboxOpen, setInboxOpen] = useState(false);
  const resend = useResendVerification(email);

  if (!email) return <StatusView icon={Mail} title="نأكد بريدك الأول" description="سجّل دخولك أو اعمل حساب عشان نبعته لك رابط تأكيد البريد."><Link className="button button-primary" to="/login">تسجيل الدخول</Link></StatusView>;

  return <>
    <BackLink to="/register">رجوع للتسجيل</BackLink>
    <StatusView icon={MailCheck} title="راجع بريدك الإلكتروني" description="رابط تأكيد بريدك جاهز. افتح الرسالة واضغط على «تأكيد البريد».">
      <div className="email-chip"><Mail size={18} aria-hidden="true" /><bdi>{email}</bdi></div>
      {appConfig.isDemo && <Button onClick={() => setInboxOpen(true)} icon={<Mail size={19} aria-hidden="true" />}>فتح البريد التجريبي</Button>}
      <p className="under-form">الرسالة ماوصلتش؟ <button type="button" className="text-link" disabled={resend.pending || resend.secondsRemaining > 0} onClick={resend.resend}>{resend.pending ? 'جاري الإرسال…' : resend.secondsRemaining > 0 ? `إعادة الإرسال بعد ${resend.secondsRemaining} ث` : 'إعادة إرسال الرابط'}</button></p>
      <FormError message={resend.error} />
      <p className="note"><Info size={17} aria-hidden="true" />{appConfig.isDemo ? 'في النسخة النهائية هتوصلك رسالة على بريدك الإلكتروني.' : 'افتح الرسالة اللي وصلت على بريدك واضغط رابط تأكيد الحساب.'}</p>
      <Link className="text-link" to="/register">كتبت البريد غلط؟ عدّله</Link>
    </StatusView>
    {appConfig.isDemo && <EmailPreview open={inboxOpen} onClose={() => setInboxOpen(false)} email={email} token={services.demo.getVerificationToken(email)} kind="verification" />}
  </>;
}
