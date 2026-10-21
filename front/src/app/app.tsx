import { createAppServices } from './services';
import { ServicesProvider } from './providers/services-provider';
import { ToastProvider } from './providers/toast-provider';
import { ErrorBoundary } from './error-boundary';
import { AppRouter } from './router/app-router';
import './config';
const services = createAppServices();
export function App() {
  return <ErrorBoundary><ServicesProvider services={services}><ToastProvider><AppRouter /></ToastProvider></ServicesProvider></ErrorBoundary>;
}
