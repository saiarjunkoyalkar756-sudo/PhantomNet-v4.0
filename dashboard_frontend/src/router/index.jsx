import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import ProtectedRoute from './ProtectedRoute';
import AdminRoute from './AdminRoute';
import Layout from '../components/shared/Layout';

const Dashboard = lazy(() => import('../pages/Dashboard'));
const LoginPage = lazy(() => import('../pages/Login'));
const CaseManagementPage = lazy(() => import('../pages/CaseManagementPage'));
const ComplianceReportingPage = lazy(() => import('../pages/ComplianceReportingPage'));
const AdminDashboard = lazy(() => import('../pages/AdminDashboard'));
const EventStreamViewer = lazy(() => import('../pages/EventStreamViewer'));
const AgentsManagementPage = lazy(() => import('../pages/AgentsManagementPage'));
const ThreatGraphIntelligencePage = lazy(() => import('../pages/ThreatGraphIntelligencePage'));
const ThreatIntelOSINTPage = lazy(() => import('../pages/ThreatIntelOSINTPage'));
const ThreatHuntingPage = lazy(() => import('../pages/ThreatHuntingPage'));
const GraphInvestigationPage = lazy(() => import('../pages/GraphInvestigationPage'));
const VulnerabilityScannerPage = lazy(() => import('../pages/VulnerabilityScannerPage'));
const CloudSecurityPage = lazy(() => import('../pages/CloudSecurityPage'));
const SiemIntegrationPage = lazy(() => import('../pages/SiemIntegrationPage'));
const SandboxPage = lazy(() => import('../pages/SandboxPage'));
const SelfHealingConsolePage = lazy(() => import('../pages/SelfHealingConsolePage'));
const AIDecisionLogPage = lazy(() => import('../pages/AIDecisionLogPage'));
const Marketplace = lazy(() => import('../pages/Marketplace'));
const LogViewer = lazy(() => import('../pages/LogViewer'));
const ConfigurationSettingsPage = lazy(() => import('../pages/ConfigurationSettingsPage'));
const SOARPage = lazy(() => import('../pages/SOARPage'));
const VulnerabilityManagementPage = lazy(() => import('../pages/VulnerabilityManagementPage'));
const SIEMPage = lazy(() => import('../pages/SIEMPage'));
const CompliancePage = lazy(() => import('../pages/CompliancePage'));
const ForensicsPage = lazy(() => import('../pages/ForensicsPage'));
const AttackGraphPage = lazy(() => import('../pages/AttackGraphPage'));

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        path: 'dashboard',
        element: (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/dashboard',
        element: (
          <ProtectedRoute>
            <AdminRoute>
              <AdminDashboard />
            </AdminRoute>
          </ProtectedRoute>
        ),
      },
      {
        path: 'events',
        element: (
          <ProtectedRoute>
            <EventStreamViewer />
          </ProtectedRoute>
        ),
      },
      {
        path: 'agents',
        element: (
          <ProtectedRoute>
            <AgentsManagementPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'threat-graph',
        element: (
          <ProtectedRoute>
            <ThreatGraphIntelligencePage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'threat-hunting',
        element: (
          <ProtectedRoute>
            <ThreatHuntingPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'graph-investigation',
        element: (
          <ProtectedRoute>
            <GraphInvestigationPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'vulnerability-scanner',
        element: (
          <ProtectedRoute>
            <VulnerabilityScannerPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'cloud-security',
        element: (
          <ProtectedRoute>
            <CloudSecurityPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'siem-integration',
        element: (
          <ProtectedRoute>
            <SiemIntegrationPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'sandbox',
        element: (
          <ProtectedRoute>
            <SandboxPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'case-management',
        element: (
          <ProtectedRoute>
            <CaseManagementPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'compliance-reporting',
        element: (
          <ProtectedRoute>
            <ComplianceReportingPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'self-healing',
        element: (
          <ProtectedRoute>
            <SelfHealingConsolePage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'ai-decision-log',
        element: (
          <ProtectedRoute>
            <AIDecisionLogPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'intel',
        element: (
          <ProtectedRoute>
            <ThreatIntelOSINTPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'marketplace',
        element: (
          <ProtectedRoute>
            <Marketplace />
          </ProtectedRoute>
        ),
      },
      {
        path: 'logs',
        element: (
          <ProtectedRoute>
            <LogViewer />
          </ProtectedRoute>
        ),
      },
      {
        path: 'settings',
        element: (
          <ProtectedRoute>
            <ConfigurationSettingsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'soar',
        element: (
          <ProtectedRoute>
            <SOARPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'vulnerability-management',
        element: (
          <ProtectedRoute>
            <VulnerabilityManagementPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'siem',
        element: (
          <ProtectedRoute>
            <SIEMPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'compliance',
        element: (
          <ProtectedRoute>
            <CompliancePage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'forensics',
        element: (
          <ProtectedRoute>
            <ForensicsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'attack-graph',
        element: (
          <ProtectedRoute>
            <AttackGraphPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);

const AppRouter = () => (
  <Suspense fallback={<div className="min-h-screen bg-background" aria-label="Loading dashboard" />}>
    <RouterProvider router={router} />
  </Suspense>
);

export default AppRouter;
