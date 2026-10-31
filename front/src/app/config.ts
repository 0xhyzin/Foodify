const source = import.meta.env.VITE_DATA_SOURCE || 'api';
if (source !== 'api') throw new Error('Foodify catalog and account data must come from the FastAPI service backed by MySQL. Set VITE_DATA_SOURCE=api.');

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api/v1' : 'http://127.0.0.1:8000/api/v1')).replace(/\/$/, '');
export const appConfig = Object.freeze({
  environment: import.meta.env.VITE_APP_ENV || import.meta.env.MODE,
  dataSource: 'api',
  isDemo: false,
  isApi: true,
  apiBaseUrl,
});
