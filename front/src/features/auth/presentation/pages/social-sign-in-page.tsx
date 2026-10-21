import { useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { ArrowLeft, CircleAlert, LogIn } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { accountDestination } from '@/app/router/paths';
import { useAction } from '@/shared/hooks/use-action';
import { BackLink } from '@/shared/ui/back-link';
import { Button } from '@/shared/ui/button';
import { PageHeading } from '@/shared/ui/page-heading';
import { StatusView } from '@/shared/ui/status-view';
import { FormError } from '@/shared/ui/form-error';
import { appConfig } from '@/app/config';

export function SocialSignInPage() {
  const { provider } = useParams();
  const navigate = useNavigate();
  const services = useServices();
  const { setUser } = useSession();
  const action = useAction();
  useEffect(() => () => services.auth.cancelProviderSignIn(), [provider, services]);

  if (provider !== 'google' && provider !== 'facebook') return <StatusView icon={CircleAlert} title="طريقة الدخول دي مش متاحة" description="تقدر تسجّل بالبريد الإلكتروني أو تختار Google أو Facebook."><Link className="button button-primary" to="/login">رجوع لتسجيل الدخول</Link></StatusView>;

  const providerName = provider === 'google' ? 'Google' : 'Facebook';
  function continueWithProvider() {
    if (provider !== 'google' && provider !== 'facebook') return;
    void action.run(() => services.auth.signInWithProvider(provider), user => {
      setUser(user);
      navigate(accountDestination(user), { replace: true });
    });
  }

  return <>
    <BackLink to="/login">رجوع لتسجيل الدخول</BackLink>
    <span className="status-icon"><LogIn size={30} aria-hidden="true" /></span>
    <PageHeading title={`متابعة باستخدام ${providerName}`} description="دخول أسهل، وبعدها نكمّل رقم موبايلك وعنوان التوصيل." />
    <div className="provider-preview"><span className="provider-initial" aria-hidden="true">{provider === 'google' ? 'G' : 'f'}</span><div><strong>{providerName}</strong><p>{appConfig.isDemo ? 'معاينة تجربة تسجيل الدخول' : 'تسجيل الدخول الآمن عبر مزود الخدمة'}</p></div></div>
    <p className="inline-notice">{appConfig.isDemo ? `دي محاكاة للواجهة. مش هنفتح حساب ${providerName} الحقيقي أو نطلب أي صلاحيات. هنستخدم حساب تجريبي عشان تستكشف الخطوات.` : `هنحوّلك إلى ${providerName} لإتمام تسجيل الدخول بأمان، وبعدها نرجعك هنا لإضافة رقمك وعنوان التوصيل.`}</p>
    <FormError message={action.error} />
    <Button loading={action.pending} onClick={continueWithProvider} icon={<ArrowLeft size={19} aria-hidden="true" />}>{appConfig.isDemo ? `متابعة تجريبية باستخدام ${providerName}` : `متابعة باستخدام ${providerName}`}</Button>
    <p className="under-form"><Link className="text-link" to="/login">أفضل الدخول بالبريد الإلكتروني</Link></p>
  </>;
}
