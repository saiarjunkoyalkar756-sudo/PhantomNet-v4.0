import React, { useEffect } from 'react';
import {
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { useSelector } from 'react-redux';

import Layout from './components/Layout'; // Import the new Layout component
import LoginPage from './components/LoginPage';
import TwoFactorAuthSetup from './components/TwoFactorAuthSetup';
import PasswordResetRequestPage from './components/PasswordResetRequestPage';
import PasswordResetConfirmPage from './components/PasswordResetConfirmPage';
import AdminDashboard from './components/AdminDashboard';
import AuditLogViewer from './components/AuditLogViewer';
import AIThreatBrain from './components/AIThreatBrain';
import NetworkMap from './components/NetworkMap';
import FederationSettings from './components/FederationSettings';
import AttackMapPage from './components/AttackMapPage';
import BlockchainViewer from './components/BlockchainViewer';
import Chatbot from './components/Chatbot'; // Import the Chatbot component
import './App.css';

import SecurityInsightsCard from './components/SecurityInsightsCard';
import HealthStatusWidget from './components/HealthStatusWidget';
import SecurityAlerts from './components/SecurityAlerts';

const DashboardContent = () => {
  const { user } = useSelector((state) => state.auth);
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center">
      <h1 className="text-4xl font-bold text-gray-800 mb-4">
        Welcome to the Dashboard, {user?.username}!
      </h1>
      <p className="text-lg text-gray-600">Your role: {user?.role}</p>
      <p className="text-lg text-gray-600">
        2FA Enabled: {user?.twofa_enabled ? 'Yes' : 'No'}
      </p>
      <p className="text-lg text-gray-600">
        2FA Enforced: {user?.twofa_enforced ? 'Yes' : 'No'}
      </p>
      <div className="mt-8 w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-4">
        <SecurityInsightsCard />
        <HealthStatusWidget />
        <div className="md:col-span-2">
          <SecurityAlerts />
        </div>
        <div className="md:col-span-2 h-96"> {/* Added Chatbot */}
          <Chatbot />
        </div>
      </div>
    </div>
  );
};

function App() {
  const { user, isAuthenticated, loading } = useSelector((state) => state.auth);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-xl">
        Loading...
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route
          path="login"
          element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />}
        />
        <Route
          path="dashboard"
          element={isAuthenticated ? <DashboardContent /> : <Navigate to="/login" />}
        />
        <Route
          path="2fa-setup"
          element={isAuthenticated ? <TwoFactorAuthSetup /> : <Navigate to="/login" />}
        />
        <Route
          path="request-password-reset"
          element={<PasswordResetRequestPage />}
        />
        <Route path="reset-password" element={<PasswordResetConfirmPage />} />
        <Route
          path="admin"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <AdminDashboard />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="admin/audit"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <AuditLogViewer />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="ai-threat-brain"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <AIThreatBrain />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="network-map"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <NetworkMap />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="attack-map"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <AttackMapPage />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="federation-settings"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <FederationSettings />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="blockchain"
          element={
            isAuthenticated && user?.role === 'admin' ? (
              <BlockchainViewer />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} />}
        />
      </Route>
    </Routes>
  );
}

export default App;
