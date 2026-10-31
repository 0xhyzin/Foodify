import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const dataSource = env.VITE_DATA_SOURCE || 'api';
  if (dataSource !== 'api') throw new Error('Foodify builds must read data from the FastAPI service backed by MySQL. Set VITE_DATA_SOURCE=api.');
  const apiBaseUrl = (env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
  let apiOrigin = '';
  try { apiOrigin = new URL(apiBaseUrl).origin; } catch { apiOrigin = ''; }
  const connectSource = dataSource === 'api'
    ? `connect-src 'self'${apiOrigin ? ` ${apiOrigin}` : ''};`
    : "connect-src 'none';";
  return {
  plugins: [react(), {
    name: 'foodify-production-csp',
    apply: 'build',
    transformIndexHtml() {
      return [{ tag: 'meta', attrs: { 'http-equiv': 'Content-Security-Policy', content: `default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data: https://talabat.dhmedia.io https://images.deliveryhero.io; ${connectSource} base-uri 'none'; form-action 'none'; object-src 'none'` }, injectTo: 'head-prepend' }];
    },
  }],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  // Keep font files on this origin so the production font-src 'self' CSP can load them.
  build: { sourcemap: false, assetsInlineLimit: 0 },
  server: { port: 5173, strictPort: true },
  };
});
