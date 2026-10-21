import { useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router';
import { FlaskConical, Info, UserRound } from 'lucide-react';
import { Dialog } from '@/shared/ui/dialog';
import { Button } from '@/shared/ui/button';
import '@/features/catalog/presentation/catalog.css';

export function CatalogLayout() {
  const [aboutOpen, setAboutOpen] = useState(false);

  return <div className="site-frame catalog-frame">
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>انتقل للمحتوى</a>
    <header className="site-header catalog-header">
      <Link to="/" className="logo" aria-label="Foodify — الصفحة الرئيسية"><span className="logo-mark" aria-hidden="true">f</span><span className="wordmark">foodify</span></Link>
      <nav className="catalog-nav" aria-label="التنقل الرئيسي"><NavLink to="/" end>المطاعم</NavLink><button type="button" onClick={() => setAboutOpen(true)} aria-label="عن تجربة المطاعم"><Info size={17} aria-hidden="true" /><span>عن التجربة</span></button></nav>
      <Link className="catalog-account-link" to="/account"><UserRound size={18} aria-hidden="true" />حسابي</Link>
    </header>
    <div className="catalog-demo-banner"><FlaskConical size={16} aria-hidden="true" /><span>لفّة تجريبية في المطاعم. اختار مطعم وشوف قائمة الأكل.</span></div>
    <main className="catalog-main" id="main-content" tabIndex={-1}><Outlet /></main>
    <footer className="site-footer catalog-footer"><Link to="/" className="catalog-footer-brand" aria-label="Foodify — الصفحة الرئيسية">foodify<span>أكلة حلوة، ويوم أحلى.</span></Link><span>بيانات تجريبية · مفيش طلبات أو دفع فعلي</span></footer>
    <Dialog open={aboutOpen} title="أهلاً بيك في تجربة المطاعم" onClose={() => setAboutOpen(false)}><p>اختار من المطاعم المعروضة، وافتح قائمة أي مطعم عشان تشوف ٣ أكلات وتفاصيل مكوناتها وأسعارها.</p><p>كل بيانات المطاعم والأكلات والتقييمات والأسعار ووقت التوصيل تجريبية للعرض. مفيش طلبات أو دفع فعلي في الجزء ده.</p><Button onClick={() => setAboutOpen(false)}>يلا نشوف المطاعم</Button></Dialog>
  </div>;
}
