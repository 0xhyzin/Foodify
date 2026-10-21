import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { KeyRound, Link2Off } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { useAction } from '@/shared/hooks/use-action';
import { BackLink } from '@/shared/ui/back-link';
import { Button } from '@/shared/ui/button';
import { PasswordField } from '@/shared/ui/field';
import { PageHeading } from '@/shared/ui/page-heading';
import { StatusView } from '@/shared/ui/status-view';
import { FormError } from '@/shared/ui/form-error';
import { useSensitiveSearchParam } from '@/shared/hooks/use-sensitive-search-param';

export function ResetPasswordPage() {
  const token = useSensitiveSearchParam('token');
  return <ResetPasswordForm key={token} token={token} />;
}

function ResetPasswordForm({ token }: { token: string }) {
  const services = useServices();
  const { setUser } = useSession();
  const navigate = useNavigate();
  const action = useAction();
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [confirmationError, setConfirmationError] = useState<string | undefined>();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== confirmation) {
      setConfirmationError('كلمتا المرور مش متطابقين. اكتب نفس الكلمة تاني.');
      requestAnimationFrame(() => document.getElementById('reset-password-confirmation')?.focus());
      return;
    }
    setConfirmationError(undefined);
    void action.run(() => services.auth.resetPassword({ token, password }), () => {
      setUser(null);
      navigate('/reset-password/success', { replace: true });
    });
  }

  if (!token) return <StatusView icon={Link2Off} title="الرابط ناقص" description="افتح الرابط كامل من رسالة تغيير كلمة المرور، أو اطلب رابط جديد."><Link className="button button-primary" to="/forgot-password">طلب رابط جديد</Link></StatusView>;

  return <>
    <BackLink to="/login">رجوع لتسجيل الدخول</BackLink>
    <span className="status-icon"><KeyRound size={30} aria-hidden="true" /></span>
    <PageHeading title="كلمة مرور جديدة" description="اختار كلمة مرور سهلة عليك وصعبة على غيرك." />
    <form className="form" noValidate onSubmit={handleSubmit}>
      <PasswordField label="كلمة المرور الجديدة" name="password" dir="ltr" autoComplete="new-password" placeholder="15 حرف على الأقل" required minLength={15} maxLength={128} value={password} onChange={event => setPassword(event.target.value)} error={action.fieldErrors.password} hint="ممكن تستخدم جملة طويلة تفتكرها بسهولة." />
      <PasswordField label="تأكيد كلمة المرور" id="reset-password-confirmation" name="passwordConfirmation" dir="ltr" autoComplete="new-password" placeholder="اكتب كلمة المرور تاني" required maxLength={128} value={confirmation} onChange={event => { setConfirmation(event.target.value); setConfirmationError(undefined); }} error={confirmationError} />
      <FormError message={action.error} />
      <Button type="submit" loading={action.pending}>حفظ كلمة المرور الجديدة</Button>
      {action.error && <Link className="text-link center" to="/forgot-password">الرابط مش شغال؟ اطلب رابط جديد</Link>}
    </form>
  </>;
}
