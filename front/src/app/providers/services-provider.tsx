import { createContext, useContext, type ReactNode } from 'react';
import type { AppServices } from '@/app/services';
const ServicesContext = createContext<AppServices | null>(null);
export function ServicesProvider({ services, children }: { services: AppServices; children: ReactNode }) {
  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>;
}
export function useServices() {
  const services = useContext(ServicesContext);
  if (!services) throw new Error('ServicesProvider is required');
  return services;
}
