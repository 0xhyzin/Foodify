import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { ArrowLeft } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useAction } from '@/shared/hooks/use-action';
import { Button } from '@/shared/ui/button';
import { Field, PasswordField } from '@/shared/ui/field';
import { PageHeading } from '@/shared/ui/page-heading';
import { FormError } from '@/shared/ui/form-error';
import { SocialButtons } from '../components/social-buttons';

export function RegisterPage() {
  const services = useServices();
  const navigate = useNavigate();
  const action = useAction();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void action.run(() => services.auth.signUp({ name, email, password }), () => navigate(`/verify-email?email=${encodeURIComponent(email.trim())}`));
  }

  return <>
    <PageHeading title="حسابك، وبداية أسهل" description="كل اللي بتحبّه، في مكان واحد." />
    <SocialButtons />
    <form className="form" noValidate onSubmit={handleSubmit}>
      <Field label="الاسم" name="name" autoComplete="name" placeholder="اسمك بالكامل" required minLength={1} maxLength={100} value={name} onChange={event => setName(event.target.value)} error={action.fieldErrors.name} />
      <Field label="البريد الإلكتروني" name="email" type="email" dir="ltr" autoComplete="email" placeholder="name@example.com" required maxLength={254} value={email} onChange={event => setEmail(event.target.value)} error={action.fieldErrors.email} />
      <PasswordField label="كلمة المرور" name="password" dir="ltr" autoComplete="new-password" placeholder="اختار كلمة مرور" required minLength={15} maxLength={128} value={password} onChange={event => setPassword(event.target.value)} error={action.fieldErrors.password} hint="15 حرف على الأقل. ممكن تستخدم جملة سهلة تفتكرها." />
      <FormError message={action.error} />
      <Button type="submit" loading={action.pending} icon={<ArrowLeft size={19} aria-hidden="true" />}>إنشاء حساب</Button>
    </form>
    <p className="under-form">عندك حساب بالفعل؟ <Link className="text-link" to="/login">تسجيل الدخول</Link></p>
  </>;
}
