import { Link } from 'react-router';

function GoogleMark() {
  return <svg viewBox="0 0 24 24" aria-hidden="true" className="provider-mark"><path fill="currentColor" d="M21.6 12.23c0-.71-.06-1.39-.18-2.05H12v3.88h5.38a4.6 4.6 0 0 1-1.99 3.01v2.5h3.22c1.88-1.73 2.99-4.28 2.99-7.34ZM12 22c2.7 0 4.96-.9 6.61-2.43l-3.22-2.5c-.9.6-2.04.97-3.39.97-2.61 0-4.83-1.76-5.62-4.13H3.06v2.58A10 10 0 0 0 12 22ZM6.38 13.91a6 6 0 0 1 0-3.82V7.51H3.06a10 10 0 0 0 0 8.98l3.32-2.58ZM12 5.96c1.47 0 2.79.51 3.82 1.51l2.87-2.87A9.61 9.61 0 0 0 12 2a10 10 0 0 0-8.94 5.51l3.32 2.58A5.98 5.98 0 0 1 12 5.96Z" /></svg>;
}

function FacebookMark() {
  return <svg viewBox="0 0 24 24" aria-hidden="true" className="provider-mark"><path fill="currentColor" d="M14 21v-8h2.7l.4-3H14V8.1c0-.9.3-1.5 1.6-1.5h1.6V3.9c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.2H8.3v3H11v8h3Z" /></svg>;
}

export function SocialButtons() {
  return <>
    <div className="social-buttons" aria-label="طرق تسجيل الدخول الأخرى">
      <Link className="button button-secondary" to="/oauth/google"><GoogleMark /><span>Google</span></Link>
      <Link className="button button-secondary" to="/oauth/facebook"><FacebookMark /><span>Facebook</span></Link>
    </div>
    <div className="divider"><span>أو باستخدام البريد الإلكتروني</span></div>
  </>;
}
