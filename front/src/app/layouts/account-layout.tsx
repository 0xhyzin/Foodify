import { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router';
import { CircleHelp, FlaskConical, RotateCcw, ShieldCheck } from 'lucide-react';
import { BrandPanel } from './brand-panel';
import { Dialog } from '@/shared/ui/dialog';
import { Button } from '@/shared/ui/button';
import { useServices } from '@/app/providers/services-provider';
import { useSession } from '@/app/providers/session-provider';
import { useToast } from '@/app/providers/toast-provider';
import { appConfig } from '@/app/config';
export function AccountLayout() {
  const [helpOpen, setHelpOpen] = useState(false);
  const [demoOpen, setDemoOpen] = useState(false);
  const services = useServices();
  const { user, setUser } = useSession();
  const { showToast } = useToast();
  const navigate = useNavigate();
  return <div className="site-frame">
    <a className="skip-link" href="#main-content" onClick={(e) => { e.preventDefault(); document.querySelector<HTMLElement>('#main-content')?.focus(); }}>انتقل للمحتوى</a>
    <header className="site-header"><Link to={user ? '/account' : '/login'} className="logo" aria-label="Foodify — الصفحة الرئيسية"><span className="logo-mark" aria-hidden="true">f</span><span className="wordmark">foodify</span></Link><div className="header-actions">{user && <Link className="account-link" to="/account">حسابي</Link>}<button type="button" className="help-button" onClick={() => setHelpOpen(true)}><CircleHelp size={18} />المساعدة</button></div></header>
    <main className="main-grid" id="main-content" tabIndex={-1}><section className="form-area" aria-label="حساب المستخدم"><div className="form-shell"><Outlet /></div></section><BrandPanel /></main>
    <footer className="site-footer"><span dir="ltr">© {new Date().getFullYear()} foodify</span><span>أكل ومقاضي، ببساطة.</span></footer>
    {appConfig.isDemo && <div className="demo-bar"><span><FlaskConical size={15} aria-hidden="true" />نسخة عرض تفاعلية</span><button type="button" className="text-link" onClick={() => setDemoOpen(true)}>عن النسخة دي</button></div>}
    <Dialog open={helpOpen} title="نقدر نساعدك إزاي؟" onClose={() => setHelpOpen(false)}><div className="help-content"><div className="status-icon"><CircleHelp size={26} /></div><h3>كل حاجة تبدأ من حسابك</h3><p>اعمل حساب ببريدك الإلكتروني، أو سجّل باستخدام Google أو Facebook. بعد كده ضيف رقمك وعنوان التوصيل.</p><h3>نسيت كلمة المرور؟</h3><p>اختار «نسيت كلمة المرور؟» في صفحة الدخول، وهنمشي معاك خطوة بخطوة.</p><h3>حابب تعدّل بياناتك؟</h3><p>من «حسابي» تقدر تعدّل الاسم والرقم وتدير عناوين التوصيل.</p><div className="note"><ShieldCheck size={18} />{appConfig.isDemo ? 'دي نسخة عرض. استخدم بيانات وهمية للتجربة.' : 'بيانات حسابك وعناوينك متاحة ليك من صفحة حسابي.'}</div><Button onClick={() => setHelpOpen(false)}>تمام، فهمت</Button></div></Dialog>
    {appConfig.isDemo && <Dialog open={demoOpen} title="عن نسخة العرض" onClose={() => setDemoOpen(false)}><p>دي تجربة تفاعلية للواجهات. تسجيل الدخول، رسائل البريد، وGoogle وFacebook محاكاة محلية، ومفيش طلبات بتتبعت للباك إند.</p><p>كلمات المرور مش بتتحفظ أو بتتراجع. أي بيانات بتدخلها موجودة في الذاكرة بس، وبتتمسح لو حدّثت الصفحة. استخدم بيانات تجريبية.</p><div className="actions"><Button onClick={() => setDemoOpen(false)}>نكمل التجربة</Button><Button variant="secondary" icon={<RotateCcw size={17} />} onClick={() => { services.demo.reset(); setUser(null); setDemoOpen(false); navigate('/login'); showToast('بدأنا تجربة جديدة.'); }}>إعادة التجربة من الأول</Button></div></Dialog>}
  </div>;
}
