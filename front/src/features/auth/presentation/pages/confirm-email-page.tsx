import { Link, useNavigate } from 'react-router';
import { MailCheck, Link2Off } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { accountDestination } from '@/app/router/paths';
import { useAction } from '@/shared/hooks/use-action';
import { Button } from '@/shared/ui/button';
import { StatusView } from '@/shared/ui/status-view';
import { FormError } from '@/shared/ui/form-error';
import { useSensitiveSearchParam } from '@/shared/hooks/use-sensitive-search-param';

export function ConfirmEmailPage() {
  const token = useSensitiveSearchParam('token');
  return <ConfirmEmailContent key={token} token={token} />;
}

function ConfirmEmailContent({ token }: { token: string }) {
  const services = useServices();
  const { setUser } = useSession();
  const navigate = useNavigate();
  const action = useAction();

  if (!token) return <StatusView icon={Link2Off} title="الرابط ناقص" description="افتح رابط التأكيد كامل من الرسالة اللي وصلتك، أو سجّل دخولك عشان تطلب رابط جديد."><Link className="button button-primary" to="/login">رجوع لتسجيل الدخول</Link></StatusView>;

  return <StatusView icon={MailCheck} title="نأكد بريدك الإلكتروني" description="اضغط على الزر عشان تأكّد البريد المرتبط بحسابك وتكمل رحلتك معانا.">
    <FormError message={action.error} />
    <Button loading={action.pending} onClick={() => void action.run(() => services.auth.confirmEmail({ token }), user => {
      setUser(user);
      navigate(accountDestination(user), { replace: true });
    })}>تأكيد البريد ومتابعة بياناتي</Button>
    {action.error && <Link className="text-link" to="/login">تسجيل الدخول وطلب رابط جديد</Link>}
  </StatusView>;
}
