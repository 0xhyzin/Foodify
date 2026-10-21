import { Link, useNavigate } from 'react-router';
import { PageHeading } from '@/shared/ui/page-heading';
import { BackLink } from '@/shared/ui/back-link';
import { OnboardingSteps } from '../components/onboarding-steps';
import { AddressForm } from '../components/address-form';
export function CompleteAddressPage() {
  const navigate = useNavigate();
  return <><BackLink to="/onboarding/profile">رجوع لبياناتك</BackLink><OnboardingSteps step={2} /><PageHeading title="نوصّلك فين؟" description="تفاصيل بسيطة تخلّي طلبك يوصل من أول مرة." /><AddressForm onSaved={() => navigate('/onboarding/complete')} /><p className="under-form"><Link className="text-link muted" to="/account">هكمّل العنوان بعدين</Link></p></>;
}
