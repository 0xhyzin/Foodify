import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { Check, X } from 'lucide-react';
const ToastContext = createContext<{ showToast(message: string): void } | null>(null);
export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showToast = useCallback((text: string) => { if (timer.current) clearTimeout(timer.current); setMessage(text); timer.current = setTimeout(() => setMessage(''), 4500); }, []);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  return <ToastContext.Provider value={{ showToast }}>{children}<div className="toast-region" aria-live="polite" aria-atomic="true">{message && <div className="toast"><Check size={18} /><span>{message}</span><button type="button" aria-label="إغلاق التنبيه" onClick={() => setMessage('')}><X size={16} /></button></div>}</div></ToastContext.Provider>;
}
export function useToast() { const toast = useContext(ToastContext); if (!toast) throw new Error('ToastProvider is required'); return toast; }
