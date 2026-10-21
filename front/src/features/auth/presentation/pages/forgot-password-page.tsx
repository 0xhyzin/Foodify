import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router';
import { KeyRound, Mail } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useAction } from '@/shared/hooks/use-action';
import { BackLink } from '@/shared/ui/back-link';
import { Button } from '@/shared/ui/button';
import { Field } from '@/shared/ui/field';
import { PageHeading } from '@/shared/ui/page-heading';
import { FormError } from '@/shared/ui/form-error';

export function ForgotPasswordPage() {
  const services = useServices();
  const navigate = useNavigate();
  const action = useAction();
  const [email, setEmail] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void action.run(() => services.auth.requestPasswordReset({ email }), () => navigate(`/reset-password/sent?email=${encodeURIComponent(email.trim())}`));
  }

  return <>
    <BackLink to="/login">رجوع لتسجيل الدخول</BackLink>
    <span className="status-icon"><KeyRound size={30} aria-hidden="true" /></span>
    <PageHeading title="نسيت كلمة المرور؟" description="اكتب بريدك الإلكتروني وهنبعتلك رابط تختار منه كلمة مرور جديدة." />
    <form className="form" noValidate onSubmit={handleSubmit}>
      <Field label="البريد الإلكتروني" name="email" type="email" dir="ltr" autoComplete="email" placeholder="name@example.com" required maxLength={254} value={email} onChange={event => setEmail(event.target.value)} error={action.fieldErrors.email} />
      <FormError message={action.error} />
      <Button type="submit" loading={action.pending} icon={<Mail size={19} aria-hidden="true" />}>إرسال رابط التغيير</Button>
    </form>
  </>;
}
