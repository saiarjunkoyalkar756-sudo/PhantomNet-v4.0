import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const ProtectedRoute = ({ children }) => {
  const { accessToken, loading } = useAuthStore((state) => ({
    accessToken: state.accessToken,
    loading: state.loading,
  }));
  const location = useLocation();

  if (loading) {
    // You can replace this with a loading spinner
    return <div>Loading...</div>;
  }

  if (!accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
