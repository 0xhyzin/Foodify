const source = import.meta.env.VITE_DATA_SOURCE || 'api';
if (source !== 'demo' && source !== 'api') throw new Error('VITE_DATA_SOURCE must be either "api" or "demo".');

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api/v1' : 'http://127.0.0.1:8000/api/v1')).replace(/\/$/, '');
export const appConfig = Object.freeze({
  environment: import.meta.env.VITE_APP_ENV || import.meta.env.MODE,
  dataSource: source,
  isDemo: source === 'demo',
  isApi: source === 'api',
  apiBaseUrl,
});
