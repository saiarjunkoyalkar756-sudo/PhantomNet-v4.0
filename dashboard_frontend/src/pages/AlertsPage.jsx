import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; // Assuming shadcn-ui Card component
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'; // Assuming shadcn-ui Table component
import { Badge } from '@/components/ui/badge'; // Assuming shadcn-ui Badge component

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const AlertsPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/api/v1/alerts`);
        setAlerts(response.data);
      } catch (err) {
        console.error("Failed to fetch alerts:", err);
        setError("Failed to load alerts. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    // Refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-4 text-center">Loading alerts...</div>;
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Security Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="text-center text-gray-500">No alerts found.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Alert ID</TableHead>
                    <TableHead>Rule Name</TableHead>
                    <TableHead>Agent ID</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Triggered At</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.alert_id}>
                      <TableCell className="font-medium">{alert.alert_id}</TableCell>
                      <TableCell>{alert.rule_name}</TableCell>
                      <TableCell>{alert.agent_id}</TableCell>
                      <TableCell>
                        <Badge variant={
                          alert.severity === 'high' ? 'destructive' : 
                          alert.severity === 'medium' ? 'warning' : 
                          'default'
                        }>
                          {alert.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(alert.triggered_at).toLocaleString()}</TableCell>
                      <TableCell className="max-w-xs overflow-hidden text-ellipsis whitespace-nowrap">{alert.details}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AlertsPage;
