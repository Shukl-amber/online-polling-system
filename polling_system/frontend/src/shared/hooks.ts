import { useState, useCallback } from 'react';
import { getCurrentUser, signOut } from 'aws-amplify/auth';

export interface AuthUser {
  userId: string;
  username: string;
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser({
        userId: currentUser.userId,
        username: currentUser.username,
      });
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSignOut = useCallback(async () => {
    await signOut();
    setUser(null);
  }, []);

  return { user, loading, checkAuth, signOut: handleSignOut };
}
