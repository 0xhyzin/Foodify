import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { LoaderCircle } from 'lucide-react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  loading?: boolean;
  icon?: ReactNode;
};
export function Button({ variant = 'primary', loading = false, icon, children, className = '', disabled, type = 'button', ...props }: ButtonProps) {
  return <button type={type} className={`button button-${variant} ${className}`} disabled={disabled || loading} aria-busy={loading || undefined} {...props}>
    {children}{loading ? <LoaderCircle size={18} className="spin" aria-hidden="true" /> : icon}
  </button>;
}
