import { useAuthStore } from '../store/auth';

export const useAuth = () => {
  const { user, token, isAuthenticated, login, logout, setUser } = useAuthStore();

  const isAdmin = user?.role === 'admin';
  const isReviewer = user?.role === 'reviewer' || user?.role === 'admin';

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    isReviewer,
    login,
    logout,
    setUser,
  };
};
