/**
 * FastAPI email/OAuth redirects use a physical path plus a fragment. The app
 * uses HashRouter, so normalize those links before React reads the hash.
 */
export function normalizeExternalLinks(): void {
  const physicalPath = window.location.pathname.replace(/\/$/, '') || '/';
  const fragment = window.location.hash.slice(1);
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
