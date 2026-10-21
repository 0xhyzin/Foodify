import { useId, useState, type InputHTMLAttributes, type ReactNode } from 'react';
import { AlertCircle, Eye, EyeOff } from 'lucide-react';

type FieldProps = InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string; labelAction?: ReactNode };
export function Field({ label, hint, error, labelAction, id, className = '', ...props }: FieldProps) {
  const generatedId = useId();
  const fieldId = id || generatedId;
  const describedBy = [hint && `${fieldId}-hint`, error && `${fieldId}-error`].filter(Boolean).join(' ');
  return <div className={`field ${className}`}>
    <div className="label-row"><label htmlFor={fieldId}>{label}</label>{labelAction}</div>
    <input {...props} id={fieldId} aria-invalid={!!error} aria-describedby={describedBy || undefined} />
    {hint && <p id={`${fieldId}-hint`} className="caption">{hint}</p>}
    {error && <p id={`${fieldId}-error`} className="field-error"><AlertCircle size={15} aria-hidden="true" />{error}</p>}
  </div>;
}
export function PasswordField({ label, hint, error, labelAction, id, ...props }: FieldProps) {
  const generatedId = useId();
  const fieldId = id || generatedId;
  const [visible, setVisible] = useState(false);
  const describedBy = [hint && `${fieldId}-hint`, error && `${fieldId}-error`].filter(Boolean).join(' ');
  return <div className="field">
    <div className="label-row"><label htmlFor={fieldId}>{label}</label>{labelAction}</div>
    <div className="password-wrap">
      <input {...props} id={fieldId} type={visible ? 'text' : 'password'} dir="ltr" aria-invalid={!!error} aria-describedby={describedBy || undefined} />
      <button className="eye-button" type="button" aria-label={visible ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={19} /> : <Eye size={19} />}</button>
    </div>
    {hint && <p id={`${fieldId}-hint`} className="caption">{hint}</p>}
    {error && <p id={`${fieldId}-error`} className="field-error"><AlertCircle size={15} aria-hidden="true" />{error}</p>}
  </div>;
}
