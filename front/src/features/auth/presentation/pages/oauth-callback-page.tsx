import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router';
import { CircleAlert, LoaderCircle } from 'lucide-react';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { accountDestination } from '@/app/router/paths';
import { StatusView } from '@/shared/ui/status-view';
import { useSensitiveSearchParam } from '@/shared/hooks/use-sensitive-search-param';
import { useAction } from '@/shared/hooks/use-action';

export function OAuthCallbackPage() {
  const ticket = useSensitiveSearchParam('ticket');
  const [params] = useSearchParams();
  const [errorCode] = useState(() => params.get('error') ?? '');
  const services = useServices();
  const { setUser } = useSession();
  const navigate = useNavigate();
  const started = useRef(false);
  const { run, error } = useAction();

  useEffect(() => {
    if (errorCode) {
      services.auth.cancelProviderSignIn();
      return;
    }
    if (!ticket || started.current) return;
    started.current = true;
    void run(() => services.auth.completeProviderSignIn({ ticket }), user => {
      setUser(user);
      navigate(accountDestination(user), { replace: true });
    });
  }, [errorCode, navigate, run, services, setUser, ticket]);

  if (errorCode) {
    return <StatusView
      icon={CircleAlert}
      title={errorCode === 'email_verification_required' ? 'أكد بريدك الإلكتروني الأول' : 'تسجيل الدخول ما اكتملش'}
      description={oauthErrorMessage(errorCode)}
    ><Link className="button button-primary" to="/login">رجوع لتسجيل الدخول</Link></StatusView>;
  }
  if (!ticket) return <StatusView icon={CircleAlert} title="الرابط ناقص" description="ابدأ تسجيل الدخول من جديد واختار Google أو Facebook."><Link className="button button-primary" to="/login">رجوع لتسجيل الدخول</Link></StatusView>;
  if (error) return <StatusView icon={CircleAlert} title="تسجيل الدخول ما اكتملش" description={error}><Link className="button button-primary" to="/login">رجوع لتسجيل الدخول</Link></StatusView>;
  return <StatusView icon={LoaderCircle} title="بنكمّل تسجيل الدخول" description="لحظات ونرجّعك لحسابك." />;
}

function oauthErrorMessage(code: string): string {
  if (code === 'email_verification_required') return 'بعتنالك رسالة لتأكيد البريد. افتح الرابط، وبعد التأكيد ارجع واختار نفس طريقة الدخول باستخدام Google أو Facebook.';
  if (code === 'invalid_oauth_state' || code === 'invalid_oauth_ticket') return 'جلسة تسجيل الدخول انتهت. ارجع وابدأ من جديد.';
  if (code === 'oauth_cancelled') return 'تم إلغاء تسجيل الدخول من مزود الخدمة.';
  if (code === 'oauth_unavailable') return 'مزود تسجيل الدخول غير متاح حاليًا.';
  if (code === 'oauth_email_required') return 'مزود الخدمة لم يرجع بريدًا إلكترونيًا صالحًا.';
  if (code === 'oauth_account_link_required') return 'البريد ده مرتبط بحساب موجود. استخدم طريقة دخوله الأصلية.';
  return 'حصلت مشكلة أثناء تسجيل الدخول. جرّب تاني.';
}
