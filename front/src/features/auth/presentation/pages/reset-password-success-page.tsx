import { Link } from 'react-router';
import { ShieldCheck } from 'lucide-react';
import { StatusView } from '@/shared/ui/status-view';

export function ResetPasswordSuccessPage() {
  return <StatusView icon={ShieldCheck} title="كلمة المرور اتغيّرت" description="تقدر دلوقتي تسجّل دخولك بكلمة المرور الجديدة."><Link className="button button-primary" to="/login">تسجيل الدخول</Link></StatusView>;
}
