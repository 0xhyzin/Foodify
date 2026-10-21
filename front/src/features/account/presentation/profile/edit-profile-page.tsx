import { useNavigate } from 'react-router';
import { useSession } from '@/app/providers/session-provider';
import { useToast } from '@/app/providers/toast-provider';
import { BackLink } from '@/shared/ui/back-link';
import { PageHeading } from '@/shared/ui/page-heading';
import { ProfileForm } from '../components/profile-form';
export function EditProfilePage() {
  const { user } = useSession();
  const { showToast } = useToast();
  const navigate = useNavigate();
  if (!user) return null;
  return <><BackLink to="/account">رجوع لحسابي</BackLink><PageHeading title="بياناتك الشخصية" description="خلّي بياناتك مظبوطة عشان التواصل يبقى أسهل." /><ProfileForm user={user} onSaved={() => { showToast('بياناتك اتحفظت بنجاح.'); navigate('/account'); }} /><p className="note">البريد الإلكتروني مرتبط بحسابك ومش قابل للتعديل من هنا.</p></>;
}
