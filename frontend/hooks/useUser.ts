import { useState } from 'react';
import { createUser } from '../lib/api/users';

export function useUser(token: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateUser = async (data: any) => {
    setLoading(true);
    setError(null);
    try {
      const user = await createUser(data, token);
      return user;
    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { handleCreateUser, loading, error };
}