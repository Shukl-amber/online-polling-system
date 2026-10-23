import { useState, type FormEvent } from 'react';
import { signIn, signUp, confirmSignUp } from 'aws-amplify/auth';
import { Button } from '../../shared/components/Button';
import { Input } from '../../shared/components/Input';
import { ErrorBanner } from '../../shared/components/index';
import styles from './Auth.module.css';

type AuthView = 'signIn' | 'signUp' | 'verify';

interface AuthPageProps {
  onAuthenticated: () => void;
}

export function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [view, setView] = useState<AuthView>('signIn');
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordChecks = {
    length: password.length >= 8,
    lower: /[a-z]/.test(password),
    upper: /[A-Z]/.test(password),
    number: /\d/.test(password),
  };

  const passwordValid = Object.values(passwordChecks).every(Boolean);

  async function handleSignIn(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await signIn({ username: email, password });
      if (result.isSignedIn) {
        onAuthenticated();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleSignUp(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!passwordValid) {
      setError('Please meet all password requirements');
      return;
    }
    setLoading(true);
    try {
      const result = await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
            name: displayName.trim(),
          },
        },
      });
      if (result.nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        setView('verify');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await confirmSignUp({ username: email, confirmationCode: code });
      // Auto sign in after verification
      const result = await signIn({ username: email, password });
      if (result.isSignedIn) {
        onAuthenticated();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.authPage}>
      <div className={styles.authCard}>
        <p className={styles.appName}>Polling System</p>

        {view === 'signIn' && (
          <>
            <h1 className={styles.authTitle}>Welcome back</h1>
            <p className={styles.authSubtitle}>
              Sign in to your account to continue
            </p>
            <form onSubmit={handleSignIn} className={styles.authForm}>
              {error && <ErrorBanner message={error} />}
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
              <Input
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="Enter your password"
              />
              <Button type="submit" fullWidth disabled={loading}>
                {loading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>
            <p className={styles.authSwitch}>
              No account yet?{' '}
              <button
                className={styles.authSwitchLink}
                onClick={() => { setView('signUp'); setError(''); }}
                type="button"
              >
                Create one
              </button>
            </p>
          </>
        )}

        {view === 'signUp' && (
          <>
            <h1 className={styles.authTitle}>Create account</h1>
            <p className={styles.authSubtitle}>
              Join the polling system
            </p>
            <form onSubmit={handleSignUp} className={styles.authForm}>
              {error && <ErrorBanner message={error} />}
              <Input
                label="Display name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                autoComplete="name"
                placeholder="Your name"
              />
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
              <Input
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                placeholder="Create a password"
              />
              <ul className={styles.passwordRules}>
                <li className={passwordChecks.length ? styles.passwordRulesMet : ''}>
                  At least 8 characters
                </li>
                <li className={passwordChecks.lower ? styles.passwordRulesMet : ''}>
                  One lowercase letter
                </li>
                <li className={passwordChecks.upper ? styles.passwordRulesMet : ''}>
                  One uppercase letter
                </li>
                <li className={passwordChecks.number ? styles.passwordRulesMet : ''}>
                  One number
                </li>
              </ul>
              <Button type="submit" fullWidth disabled={loading || !passwordValid}>
                {loading ? 'Creating account...' : 'Create account'}
              </Button>
            </form>
            <p className={styles.authSwitch}>
              Already have an account?{' '}
              <button
                className={styles.authSwitchLink}
                onClick={() => { setView('signIn'); setError(''); }}
                type="button"
              >
                Sign in
              </button>
            </p>
          </>
        )}

        {view === 'verify' && (
          <>
            <h1 className={styles.authTitle}>Check your email</h1>
            <p className={styles.authSubtitle}>
              We sent a verification code to {email}
            </p>
            <form onSubmit={handleVerify} className={styles.authForm}>
              {error && <ErrorBanner message={error} />}
              <Input
                label="Verification code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                autoComplete="one-time-code"
                placeholder="Enter 6-digit code"
              />
              <Button type="submit" fullWidth disabled={loading || code.length < 6}>
                {loading ? 'Verifying...' : 'Verify and sign in'}
              </Button>
            </form>
            <p className={styles.authSwitch}>
              <button
                className={styles.authSwitchLink}
                onClick={() => { setView('signIn'); setError(''); }}
                type="button"
              >
                Back to sign in
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
