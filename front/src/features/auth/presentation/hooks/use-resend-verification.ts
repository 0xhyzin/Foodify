import { useEffect, useState } from 'react';
import { useServices } from '@/app/providers/services-provider';
import { useToast } from '@/app/providers/toast-provider';
import { useAction } from '@/shared/hooks/use-action';
import { appConfig } from '@/app/config';
import { AppError } from '@/shared/domain/app-error';

export function useResendVerification(email: string) {
  const services = useServices();
  const { showToast } = useToast();
  const action = useAction();
  const [secondsRemaining, setSecondsRemaining] = useState(0);

  useEffect(() => {
    if (secondsRemaining <= 0) return;
    const timer = window.setTimeout(() => setSecondsRemaining(value => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [secondsRemaining]);

  function resend() {
    if (secondsRemaining > 0 || action.pending) return;
    void action.run(async () => {
      try {
        await services.auth.resendVerification({ email });
      } catch (error) {
        if (error instanceof AppError && error.status === 429) {
          setSecondsRemaining(error.retryAfterSeconds ?? 60);
        }
        throw error;
      }
    }, () => {
      setSecondsRemaining(60);
      showToast(appConfig.isDemo ? 'رابط التأكيد الجديد جاهز في البريد التجريبي.' : 'لو البريد محتاج تأكيد، هتوصلك رسالة جديدة.');
    });
  }

  return { ...action, secondsRemaining, resend };
}
