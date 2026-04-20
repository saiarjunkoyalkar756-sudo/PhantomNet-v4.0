import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { LoaderCircle, Bell, Shield, Users, HeartPulse } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const AdminDashboard = () => {
  const [alertsSummary, setAlertsSummary] = useState({ total: 0, high: 0, medium: 0, low: 0 });
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    const fetchAlertsSummary = async () => {
      try {
        setLoadingAlerts(true);
        const response = await axios.get(`${API_BASE_URL}/api/v1/alerts`);
        const allAlerts = response.data;

        const summary = {
          total: allAlerts.length,
          high: allAlerts.filter(alert => alert.severity === 'high').length,
          medium: allAlerts.filter(alert => alert.severity === 'medium').length,
          low: allAlerts.filter(alert => alert.severity === 'low').length,
        };
        setAlertsSummary(summary);
      } catch (err) {
        console.error("Failed to fetch alerts summary:", err);
        setApiError("Failed to load alerts data.");
      } finally {
        setLoadingAlerts(false);
      }
    };

    fetchAlertsSummary();
    const interval = setInterval(fetchAlertsSummary, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);


  if (apiError) {
    return <div className="p-4 text-center text-red-500">{apiError}</div>;
  }

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold text-primary">Admin Dashboard</h1>
      <p className="text-muted-foreground">Comprehensive overview of your PhantomNet deployment.</p>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loadingAlerts ? (
              <LoaderCircle className="h-6 w-6 animate-spin text-primary" />
            ) : (
              <div className="text-2xl font-bold">{alertsSummary.total}</div>
            )}
            <p className="text-xs text-muted-foreground">
              {alertsSummary.high} High, {alertsSummary.medium} Medium
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div> {/* Placeholder */}
            <p className="text-xs text-muted-foreground">
              +3 since last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div> {/* Placeholder */}
            <p className="text-xs text-muted-foreground">
              +1 new user this week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <HeartPulse className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">Operational</div> {/* Placeholder */}
            <p className="text-xs text-muted-foreground">
              All services running
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Placeholder for more detailed sections */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Detailed list of recent alerts will go here.</p>
            {/* Link to AlertsPage */}
            <a href="/alerts" className="text-primary hover:underline mt-2 inline-block">View All Alerts</a>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Agent Management Quick Links</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Manage agent deployments, policies, and status.</p>
            {/* Link to AgentsManagementPage */}
            <a href="/agents" className="text-primary hover:underline mt-2 inline-block">Go to Agents</a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
