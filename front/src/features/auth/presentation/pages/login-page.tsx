import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { accountDestination } from '@/app/router/paths';
import { AppError } from '@/shared/domain/app-error';
import { useAction } from '@/shared/hooks/use-action';
import { Button } from '@/shared/ui/button';
import { Field, PasswordField } from '@/shared/ui/field';
import { PageHeading } from '@/shared/ui/page-heading';
import { FormError } from '@/shared/ui/form-error';
import { SocialButtons } from '../components/social-buttons';
import { appConfig } from '@/app/config';

export function LoginPage() {
  const navigate = useNavigate();
  const services = useServices();
  const { setUser } = useSession();
  const action = useAction();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void action.run(async () => {
      try {
        return await services.auth.signIn({ email, password });
      } catch (error) {
        if (error instanceof AppError && (error.code === 'email_not_verified' || error.code === 'email_verification_required')) navigate(`/verify-email?email=${encodeURIComponent(email.trim())}`);
        throw error;
      }
    }, user => {
      setUser(user);
      navigate(accountDestination(user), { replace: true });
    });
  }

  function fillDemoAccount() {
    setEmail('mariam@example.com');
    setPassword('Demo Foodify account!');
    action.clearError();
  }

  return <>
    <PageHeading title="أهلًا بيك تاني" description="أكلك ومقاضيك، أقرب بخطوة." />
    <SocialButtons />
    <form className="form" noValidate onSubmit={handleSubmit}>
      <Field label="البريد الإلكتروني" name="email" type="email" dir="ltr" autoComplete="email" placeholder="name@example.com" required maxLength={254} value={email} onChange={event => setEmail(event.target.value)} error={action.fieldErrors.email} />
      <PasswordField label="كلمة المرور" name="password" dir="ltr" autoComplete="current-password" placeholder="أدخل كلمة المرور" required maxLength={128} value={password} onChange={event => setPassword(event.target.value)} error={action.fieldErrors.password} labelAction={<Link className="text-link" to="/forgot-password">نسيت كلمة المرور؟</Link>} />
      <FormError message={action.error} />
      <Button type="submit" loading={action.pending} icon={<ArrowLeft size={19} aria-hidden="true" />}>تسجيل الدخول</Button>
    </form>
    <p className="under-form">أول مرة هنا؟ <Link className="text-link" to="/register">اعمل حساب</Link></p>
    {appConfig.isDemo && <div className="demo-account"><Sparkles size={18} aria-hidden="true" /><div><span>تحب تستكشف الأول؟</span><button type="button" className="text-link" onClick={fillDemoAccount}>املأ بيانات الحساب التجريبي</button></div></div>}
  </>;
}
