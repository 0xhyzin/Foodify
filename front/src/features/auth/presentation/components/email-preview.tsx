import { Link } from 'react-router';
import { Mail, ShieldCheck } from 'lucide-react';
import { Dialog } from '@/shared/ui/dialog';

interface EmailPreviewProps {
  open: boolean;
  onClose: () => void;
  email: string;
  token: string | null;
  kind: 'verification' | 'reset';
}

export function EmailPreview({ open, onClose, email, token, kind }: EmailPreviewProps) {
  const isReset = kind === 'reset';
  const link = isReset ? `/reset-password?token=${encodeURIComponent(token ?? '')}` : `/verify-email/confirm?token=${encodeURIComponent(token ?? '')}`;
  return <Dialog open={open} onClose={onClose} title={isReset ? 'رسالة تغيير كلمة المرور' : 'رسالة تأكيد البريد'}>
    <div className="email-preview">
      <div className="email-preview-sender"><span className="email-avatar"><Mail size={22} aria-hidden="true" /></span><div><strong>Foodify</strong><span>صندوق البريد التجريبي</span></div></div>
      <p className="note">إلى <bdi>{email}</bdi></p>
      {token ? <>
        <h3>{isReset ? 'نرجّعلك الوصول لحسابك' : 'أهلًا بيك في Foodify'}</h3>
        <p>{isReset ? 'اضغط على الزر واختار كلمة مرور جديدة لحسابك.' : 'فاضل ضغطة واحدة عشان تأكّد بريدك وتكمّل بياناتك.'}</p>
        <Link className="button button-primary" to={link} onClick={onClose}><ShieldCheck size={19} aria-hidden="true" />{isReset ? 'اختيار كلمة مرور جديدة' : 'تأكيد البريد الإلكتروني'}</Link>
        <p className="note">الرسالة دي جزء من تجربة الواجهة وبتتولد على جهازك فقط.</p>
      </> : <>
        <h3>مفيش رسالة متاحة حاليًا</h3>
        <p>{isReset ? 'لو عندك حساب تجريبي بالبريد ده، اطلب رابط جديد. وتقدر كمان تنشئ حساب من صفحة التسجيل.' : 'اطلب إرسال رابط جديد، وبعدها افتح صندوق البريد التجريبي تاني.'}</p>
      </>}
    </div>
  </Dialog>;
}
