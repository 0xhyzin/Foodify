import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { PageHeading } from './page-heading';
export function StatusView({ icon: Icon, title, description, children }: { icon: LucideIcon; title: string; description: string; children?: ReactNode }) {
  return <div className="status-view"><div className="status-icon"><Icon size={29} aria-hidden="true" /></div><PageHeading title={title} description={description} />{children}</div>;
}
