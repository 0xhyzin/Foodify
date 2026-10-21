import { Link } from 'react-router';
import { PartyPopper } from 'lucide-react';
import { useSession } from '@/app/providers/session-provider';
import { StatusView } from '@/shared/ui/status-view';
export function AccountReadyPage() {
  const { user } = useSession();
  return <StatusView icon={PartyPopper} title={`كل حاجة جاهزة يا ${user?.name.split(' ')[0] || 'صديقنا'}`} description="رقمك وعنوانك اتحفظوا. تقدر تراجعهم أو تغيّرهم في أي وقت من حسابك."><Link to="/account" className="button button-primary">الذهاب لحسابي</Link></StatusView>;
}
