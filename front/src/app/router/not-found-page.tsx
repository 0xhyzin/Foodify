import { Link } from 'react-router';
import { MapPinOff } from 'lucide-react';
import { StatusView } from '@/shared/ui/status-view';
import { useSession } from '@/app/providers/session-provider';
export function NotFoundPage() { const { user } = useSession(); return <StatusView icon={MapPinOff} title="الصفحة دي مش موجودة" description="ممكن الرابط يكون اتغيّر. نرجع لصفحة معروفة؟"><Link className="button button-primary" to={user ? '/account' : '/login'}>الرجوع للصفحة الرئيسية</Link></StatusView>; }
