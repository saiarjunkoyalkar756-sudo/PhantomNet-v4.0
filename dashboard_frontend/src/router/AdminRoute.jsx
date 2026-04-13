import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const AdminRoute = ({ children }) => {
  const { role, loading } = useAuthStore((state) => ({
    role: state.role,
    loading: state.loading,
  }));
  const location = useLocation();

  if (loading) {
    // You can replace this with a loading spinner
    return <div>Loading...</div>;
  }
  
  if (role !== 'admin') {
      // You can show an "Access Denied" toast message here
      return <Navigate to="/dashboard" state={{ from: location }} replace />;
  }

  return children;
};

export default AdminRoute;
