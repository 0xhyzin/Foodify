import { Check } from 'lucide-react';
export function OnboardingSteps({ step }: { step: 1 | 2 }) {
  return <ol className="steps" aria-label={`الخطوة ${step} من 2`}>
    <li className={step === 1 ? 'current' : 'completed'} aria-current={step === 1 ? 'step' : undefined}><span>{step === 2 ? <Check size={12} /> : '1'}</span>بياناتك</li>
    <li className="step-line" aria-hidden="true" />
    <li className={step === 2 ? 'current' : ''} aria-current={step === 2 ? 'step' : undefined}><span>2</span>عنوانك</li>
  </ol>;
}
