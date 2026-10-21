import { Navigate, Outlet } from 'react-router';
import { useSession } from '@/app/providers/session-provider';
import { LoadingState } from '@/shared/ui/loading-state';
import { accountDestination } from './paths';
export function RequireSession() {
  const { user, loading } = useSession();
  if (loading) return <LoadingState />;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
export function GuestOnly() {
  const { user, loading } = useSession();
  if (loading) return <LoadingState />;
  return user ? <Navigate to={accountDestination(user)} replace /> : <Outlet />;
}
export function RequirePhone() {
  const { user } = useSession();
  return user?.phoneNumber ? <Outlet /> : <Navigate to="/onboarding/profile" replace />;
}
export function RequireCompleteProfile() {
  const { user } = useSession();
  return user?.profileComplete ? <Outlet /> : <Navigate to={user ? accountDestination(user) : '/login'} replace />;
}
