import { useEffect } from 'react';
import { useLocation } from 'react-router';
const pageTitles: Record<string, string> = { '/login': 'تسجيل الدخول', '/register': 'إنشاء حساب', '/verify-email': 'تأكيد البريد', '/verify-email/confirm': 'تأكيد البريد', '/forgot-password': 'نسيت كلمة المرور', '/reset-password': 'كلمة مرور جديدة', '/reset-password/sent': 'راجع بريدك', '/reset-password/success': 'تم تغيير كلمة المرور', '/onboarding/profile': 'بياناتك', '/onboarding/address': 'عنوان التوصيل', '/onboarding/complete': 'حسابك جاهز', '/carts': 'سلالي', '/orders': 'طلباتي', '/operations': 'إدارة الطلبات', '/account': 'حسابي', '/account/edit': 'تعديل بياناتي', '/account/addresses': 'عناويني', '/account/addresses/new': 'عنوان جديد' };
export function RouteEffects() {
  const { pathname } = useLocation();
  useEffect(() => {
    document.title = `Foodify — ${pathname === '/' ? 'مطاعم على ذوقك' : pathname.startsWith('/restaurants/') ? 'قائمة المتجر' : pathname.startsWith('/checkout/') ? 'تأكيد الطلب والدفع' : pathname.startsWith('/orders/') ? 'تفاصيل وتتبع الطلب' : pageTitles[pathname] || 'Foodify'}`;
    window.scrollTo({ top: 0, behavior: 'instant' });
    const timer = setTimeout(() => (document.querySelector<HTMLElement>('h1') ?? document.getElementById('main-content'))?.focus({ preventScroll: true }), 50);
    return () => clearTimeout(timer);
  }, [pathname]);
  return null;
}
