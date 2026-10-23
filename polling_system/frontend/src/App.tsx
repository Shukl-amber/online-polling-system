import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Amplify } from 'aws-amplify';
import { Vote, LogOut, User as UserIcon } from 'lucide-react';
import { useAuth } from './shared/hooks';
import { AuthPage } from './features/auth/AuthPage';
import { PollsListPage } from './features/polls_list/PollsListPage';
import { CreatePollPage } from './features/create_poll/CreatePollPage';
import { PollDetailPage } from './features/poll_detail/PollDetailPage';
import { Skeleton } from './shared/components/index';
import styles from './App.module.css';

// Configure AWS Amplify Auth with Cognito credentials from env
const userPoolId = import.meta.env.VITE_USER_POOL_ID || '';
const userPoolClientId = import.meta.env.VITE_USER_POOL_CLIENT_ID || '';

if (userPoolId && userPoolClientId) {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId,
      },
    },
  });
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

interface TopBarProps {
  user: { username: string } | null;
  onSignOut: () => void;
}

function TopBar({ user, onSignOut }: TopBarProps) {
  return (
    <header className={styles.topBar}>
      <div className={styles.topBarInner}>
        <Link to="/polls" className={styles.brand}>
          <Vote className={styles.brandIcon} size={22} strokeWidth={2} />
          <span>Polling System</span>
        </Link>

        <div className={styles.userMenu}>
          {user ? (
            <>
              <div className={styles.userInfo}>
                <UserIcon size={16} strokeWidth={2} />
                <span>{user.username}</span>
              </div>
              <button
                type="button"
                className={styles.signOutButton}
                onClick={onSignOut}
                aria-label="Sign out"
              >
                <LogOut size={16} strokeWidth={2} />
                <span>Sign out</span>
              </button>
            </>
          ) : (
            <Link to="/auth" className={styles.signOutButton}>
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

function AppRoutes() {
  const { user, loading, checkAuth, signOut } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (loading) {
    return (
      <div className={styles.loadingCenter}>
        <div style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Skeleton height="2rem" />
          <Skeleton height="1.25rem" width="70%" />
        </div>
      </div>
    );
  }

  const handleAuthenticated = () => {
    checkAuth();
    navigate('/polls');
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/auth');
  };

  return (
    <div className={styles.appContainer}>
      <TopBar user={user} onSignOut={handleSignOut} />
      <main className={styles.mainContent}>
        <Routes>
          <Route
            path="/auth"
            element={
              user ? (
                <Navigate to="/polls" replace />
              ) : (
                <AuthPage onAuthenticated={handleAuthenticated} />
              )
            }
          />
          <Route
            path="/polls"
            element={
              user ? <PollsListPage /> : <Navigate to="/auth" replace />
            }
          />
          <Route
            path="/polls/new"
            element={
              user ? <CreatePollPage /> : <Navigate to="/auth" replace />
            }
          />
          <Route
            path="/polls/:id"
            element={
              user ? <PollDetailPage /> : <Navigate to="/auth" replace />
            }
          />
          <Route path="/" element={<Navigate to="/polls" replace />} />
          <Route path="*" element={<Navigate to="/polls" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
