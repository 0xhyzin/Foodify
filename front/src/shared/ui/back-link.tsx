import type { ReactNode } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router';
export function BackLink({ to, children = 'رجوع لتسجيل الدخول' }: { to: string; children?: ReactNode }) {
  return <Link to={to} className="back-link"><ArrowRight size={16} aria-hidden="true" />{children}</Link>;
}
