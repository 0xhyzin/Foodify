import { useCallback, useEffect, useRef, useState } from 'react';
import { AppError, getErrorMessage } from '@/shared/domain/app-error';
export function useAction() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const locked = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  const clearError = useCallback(() => { setError(null); setFieldErrors({}); }, []);
  const run = useCallback(async <T,>(action: () => Promise<T>, onSuccess?: (result: T) => void | Promise<void>) => {
    if (locked.current) return;
    locked.current = true;
    setPending(true);
    clearError();
    try {
      const result = await action();
      if (!mounted.current) return;
      await onSuccess?.(result);
    } catch (cause) {
      if (!mounted.current) return;
      setError(getErrorMessage(cause));
      setFieldErrors(cause instanceof AppError ? cause.fields || {} : {});
      requestAnimationFrame(() => { if (mounted.current) document.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(); });
    } finally { locked.current = false; if (mounted.current) setPending(false); }
  }, [clearError]);
  return { run, pending, error, fieldErrors, clearError };
}
