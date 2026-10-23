import { type InputHTMLAttributes, forwardRef, useId } from 'react';
import styles from './Input.module.css';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  function Input({ label, error, hint, className, ...props }, ref) {
    const id = useId();
    const errorId = `${id}-error`;
    const hintId = `${id}-hint`;

    return (
      <div className={styles.field}>
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
        <input
          ref={ref}
          id={id}
          className={`${styles.input} ${error ? styles.hasError : ''} ${className ?? ''}`}
          aria-invalid={error ? true : undefined}
          aria-describedby={
            [error ? errorId : '', hint ? hintId : ''].filter(Boolean).join(' ') || undefined
          }
          {...props}
        />
        {hint && !error && (
          <span id={hintId} className={styles.hint}>
            {hint}
          </span>
        )}
        {error && (
          <span id={errorId} className={styles.error} role="alert">
            {error}
          </span>
        )}
      </div>
    );
  },
);
