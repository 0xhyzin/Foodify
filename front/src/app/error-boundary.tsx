import { Component, type ErrorInfo, type ReactNode } from 'react';
export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) { /* Integration may attach a sanitized error reporter here. */ }
  render() {
    if (this.state.failed) return <main className="fatal-error" dir="rtl"><h1>حصلت مشكلة في عرض الصفحة</h1><p>حدّث الصفحة وجرّب تاني.</p><button className="button button-primary" onClick={() => window.location.reload()}>تحديث الصفحة</button></main>;
    return this.props.children;
  }
}
