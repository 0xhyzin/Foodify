import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import type { UserProfile } from '@/features/account/domain/models';
import { useServices } from './services-provider';
type SessionContextValue = { user: UserProfile | null; loading: boolean; refresh(): Promise<UserProfile | null>; setUser(user: UserProfile | null): void };
const SessionContext = createContext<SessionContextValue | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const services = useServices();
  const [user, setCurrentUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const revision = useRef(0);
  const currentUser = useRef<UserProfile | null>(null);
  const setUser = useCallback((next: UserProfile | null) => {
    revision.current += 1;
    currentUser.current = next;
    setCurrentUser(next);
  }, []);
  const refresh = useCallback(async () => {
    const startedAt = revision.current;
    const current = await services.auth.getSession();
    if (startedAt !== revision.current) return currentUser.current;
    setUser(current);
    return current;
  }, [services, setUser]);
  useEffect(() => {
    let active = true;
    const unsubscribe = services.auth.onSessionInvalidated(() => {
      if (active) setUser(null);
    });
    const startedAt = revision.current;
    services.auth.getSession()
      .then(current => { if (active && startedAt === revision.current) setUser(current); })
      .catch(() => { if (active && startedAt === revision.current) setUser(null); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; unsubscribe(); };
  }, [services, setUser]);
  return <SessionContext.Provider value={{ user, loading, refresh, setUser }}>{children}</SessionContext.Provider>;
}
export function useSession() { const session = useContext(SessionContext); if (!session) throw new Error('SessionProvider is required'); return session; }
