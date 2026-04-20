import LoginPage from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import AdminDashboard from '../pages/AdminDashboard';
import EventStreamViewer from '../pages/EventStreamViewer';
import AgentsManagementPage from '../pages/AgentsManagementPage';
import ThreatGraphIntelligencePage from '../pages/ThreatGraphIntelligencePage';
import ThreatIntelOSINTPage from '../pages/ThreatIntelOSINTPage';
import ThreatHuntingPage from '../pages/ThreatHuntingPage';
import GraphInvestigationPage from '../pages/GraphInvestigationPage';
import VulnerabilityScannerPage from '../pages/VulnerabilityScannerPage';
import CloudSecurityPage from '../pages/CloudSecurityPage';
import SiemIntegrationPage from '../pages/SiemIntegrationPage';
import SandboxPage from '../pages/SandboxPage';
import SelfHealingConsolePage from '../pages/SelfHealingConsolePage';
import AIDecisionLogPage from '../pages/AIDecisionLogPage';
import Marketplace from '../pages/Marketplace';
import LogViewer from '../pages/LogViewer';
import ConfigurationSettingsPage from '../pages/ConfigurationSettingsPage';
import ProtectedRoute from './ProtectedRoute';
import AdminRoute from './AdminRoute';
import Layout from '../components/shared/Layout';
import SOARPage from '../pages/SOARPage';
import VulnerabilityManagementPage from '../pages/VulnerabilityManagementPage';
import SIEMPage from '../pages/SIEMPage';
import CompliancePage from '../pages/CompliancePage';
import ForensicsPage from '../pages/ForensicsPage';
import AttackGraphPage from '../pages/AttackGraphPage';

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

const AppRouter = () => <RouterProvider router={router} />;

export default AppRouter;
