import { AlertCircle } from 'lucide-react';
export function FormError({ message }: { message?: string | null }) {
  return message ? <div className="form-error" role="alert"><AlertCircle size={18} aria-hidden="true" /><span>{message}</span></div> : null;
}
