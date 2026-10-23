import {
  type ReactNode,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
} from 'react';
import styles from './ui.module.css';

/* ---- Card ---- */

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={`${styles.card} ${className ?? ''}`}>
      {children}
    </div>
  );
}

/* ---- Skeleton ---- */

interface SkeletonProps {
  width?: string;
  height?: string;
}

export function Skeleton({ width = '100%', height = '1rem' }: SkeletonProps) {
  return <div className={styles.skeleton} style={{ width, height }} />;
}

/* ---- Badge ---- */

interface BadgeProps {
  status: 'open' | 'closed';
}

export function Badge({ status }: BadgeProps) {
  return (
    <span
      className={`${styles.badge} ${status === 'open' ? styles.badgeOpen : styles.badgeClosed}`}
    >
      {status}
    </span>
  );
}

/* ---- Empty State ---- */

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className={styles.emptyState}>
      {icon}
      <h2 className={styles.emptyTitle}>{title}</h2>
      <p className={styles.emptyText}>{description}</p>
      {action}
    </div>
  );
}

/* ---- Error Banner ---- */

interface ErrorBannerProps {
  message: string;
  action?: ReactNode;
}

export function ErrorBanner({ message, action }: ErrorBannerProps) {
  return (
    <div className={styles.errorBanner} role="alert">
      <span>{message}</span>
      {action}
    </div>
  );
}

/* ---- Success Banner ---- */

interface SuccessBannerProps {
  message: string;
}

export function SuccessBanner({ message }: SuccessBannerProps) {
  return (
    <div className={styles.successBanner} role="status">
      <span>{message}</span>
    </div>
  );
}

/* ---- Confirm Dialog ---- */

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  body: string;
  confirmLabel: string;
  confirmVariant?: 'primary' | 'danger';
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  onConfirm,
  onCancel,
  loading,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    },
    [onCancel],
  );

  useEffect(() => {
    if (open && dialogRef.current) {
      dialogRef.current.focus();
    }
  }, [open]);

  if (!open) return null;

  return (
    <div
      className={styles.dialogOverlay}
      onClick={onCancel}
      onKeyDown={handleKeyDown}
      role="presentation"
    >
      <div
        ref={dialogRef}
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="dialog-title" className={styles.dialogTitle}>
          {title}
        </h2>
        <p className={styles.dialogBody}>{body}</p>
        <div className={styles.dialogActions}>
          <button
            className={`${styles.badge}`}
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: '12px 20px',
              fontSize: '0.875rem',
              fontWeight: 500,
              backgroundColor: 'var(--color-surface-alt)',
              color: 'var(--color-text)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              cursor: 'pointer',
              minHeight: '44px',
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: '12px 20px',
              fontSize: '0.875rem',
              fontWeight: 500,
              backgroundColor: 'var(--color-danger)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
              minHeight: '44px',
            }}
          >
            {loading ? 'Closing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
