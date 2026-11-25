/** Enter the configured local frontend origin before starting browser sessions. */
export function redirectLocalDevelopmentOrigin(): boolean {
  if (!import.meta.env.DEV
    || window.location.protocol !== 'http:'
    || window.location.hostname !== 'localhost'
    || window.location.port !== '5173') return false;

  // OAuth verifiers belong to this tab's exact origin. The local callback uses
  // 127.0.0.1, so enter that origin before creating or reading any verifier.
  const destination = new URL(window.location.href);
  destination.hostname = '127.0.0.1';
  window.location.replace(destination.href);
  return true;
}

const DIRECT_PORTAL_PATHS = [
  '/admin',
  '/operations',
  '/manager',
  '/kitchen',
  '/delivery',
  '/login',
  '/register',
  '/orders',
  '/notifications',
];

/** Convert external action and clean portal links to HashRouter routes before React reads them. */
export function normalizeExternalLinks(): void {
  const physicalPath = window.location.pathname.replace(/\/$/, '') || '/';
  const fragment = window.location.hash.slice(1);
  if (!fragment && DIRECT_PORTAL_PATHS.includes(physicalPath)) {
    window.history.replaceState(null, document.title, `/#${physicalPath}${window.location.search}`);
    return;
  }
  if (!fragment || !['/verify-email', '/reset-password', '/oauth/callback'].includes(physicalPath)) return;

  const params = new URLSearchParams(fragment);
  let route: string;
  if (physicalPath === '/verify-email' && params.has('token')) route = `/verify-email/confirm?token=${encodeURIComponent(params.get('token') ?? '')}`;
  else if (physicalPath === '/reset-password' && params.has('token')) route = `/reset-password?token=${encodeURIComponent(params.get('token') ?? '')}`;
  else if (physicalPath === '/oauth/callback' && params.has('ticket')) route = `/oauth/callback?ticket=${encodeURIComponent(params.get('ticket') ?? '')}`;
  else if (physicalPath === '/oauth/callback' && params.has('error')) route = `/oauth/callback?error=${encodeURIComponent(params.get('error') ?? '')}`;
  else return;

  window.history.replaceState(null, document.title, `${physicalPath}#${route}`);
}
