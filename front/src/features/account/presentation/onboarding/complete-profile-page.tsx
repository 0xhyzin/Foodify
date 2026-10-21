import { useNavigate } from 'react-router';
import { useSession } from '@/app/providers/session-provider';
import { PageHeading } from '@/shared/ui/page-heading';
import { OnboardingSteps } from '../components/onboarding-steps';
import { ProfileForm } from '../components/profile-form';
export function CompleteProfilePage() {
  const { user } = useSession();
  const navigate = useNavigate();
  if (!user) return null;
  return <><OnboardingSteps step={1} /><PageHeading title="نتعرّف عليك أكتر؟" description="ضيف رقمك عشان نقدر نوصّل طلبك بسهولة." /><ProfileForm user={user} onboarding onSaved={() => navigate('/onboarding/address')} /></>;
}
