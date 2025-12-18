'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useUserStore, type UserProfile } from '@/stores/user';

// Mock API functions (replace with actual API calls)
const authApi = {
  login: async (email: string, password: string): Promise<{ token: string; user: UserProfile }> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  logout: async (): Promise<void> => {
    // TODO: Replace with actual API call
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  },
  
  register: async (data: {
    email: string;
    password: string;
    name: string;
    role: 'student' | 'teacher';
  }): Promise<{ token: string; user: UserProfile }> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  getCurrentUser: async (): Promise<UserProfile> => {
    // TODO: Replace with actual API call
    // Check if token exists
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }
    }
    throw new Error('Not implemented');
  },
  
  updateProfile: async (updates: Partial<UserProfile>): Promise<UserProfile> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
};

export function useAuth() {
  const queryClient = useQueryClient();
  const { setProfile, setAuthenticated, setLoading, setError, logout: storeLogout } = useUserStore();

  const userQuery = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      setLoading(true);
      try {
        const user = await authApi.getCurrentUser();
        setProfile(user);
        setAuthenticated(true);
        setError(null);
        return user;
      } catch (error) {
        setProfile(null);
        setAuthenticated(false);
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch user';
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (data) => {
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', data.token);
      }
      setProfile(data.user);
      setAuthenticated(true);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setError(errorMessage);
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', data.token);
      }
      setProfile(data.user);
      setAuthenticated(true);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      setError(errorMessage);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      storeLogout();
      queryClient.clear();
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (updatedUser) => {
      setProfile(updatedUser);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: ({ oldPassword, newPassword }: { oldPassword: string; newPassword: string }) =>
      authApi.changePassword(oldPassword, newPassword),
  });

  return {
    user: userQuery.data ?? null,
    isLoading: userQuery.isLoading,
    isAuthenticated: useUserStore.getState().isAuthenticated,
    error: userQuery.error,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout: logoutMutation.mutate,
    updateProfile: updateProfileMutation.mutate,
    changePassword: changePasswordMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
  };
}

