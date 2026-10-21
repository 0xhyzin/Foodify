import { Link } from 'react-router';
import { MapPinOff } from 'lucide-react';
import { StatusView } from '@/shared/ui/status-view';
export function NotFoundPage() { return <StatusView icon={MapPinOff} title="الصفحة دي مش موجودة" description="ممكن الرابط يكون اتغيّر. تقدر ترجع وتشوف المطاعم."><Link className="button button-primary" to="/">الرجوع للصفحة الرئيسية</Link></StatusView>; }
