import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { ShieldCheck, Cpu, AlertCircle, Settings, XCircle } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'react-toastify';

const SelfHealingConsolePage = () => {
  const [agentHealth, setAgentHealth] = useState(null);
  const [recentErrors, setRecentErrors] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAgentStatus();
    const interval = setInterval(fetchAgentStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAgentStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // This is a placeholder for fetching a specific agent's status or a summary
      // For now, it will fetch from a mock endpoint or a single agent's data.
      // In a real scenario, you'd select an agent from a list.
      const agentId = 1; // Example agent ID
      const response = await fetch(`/api/agents/${agentId}`); 
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch agent status');
      
      const data = await response.json();
      setAgentHealth({
        status: data.status,
        os: data.os,
        capabilities: data.capabilities,
        self_healing_enabled: data.self_healing_enabled,
        safe_mode_active: data.safe_mode_active,
        last_reported_health: data.last_reported_health,
        last_seen: data.last_seen
      });
      setRecentErrors(data.last_reported_errors || []);

    } catch (err) {
      console.error("Error fetching agent status:", err);
      setError(err.message);
      toast.error(`Error fetching agent status: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualOverride = (action) => {
    toast.info(`Manual override for: ${action} (Not Implemented)`);
    // In a real scenario, this would send a command to the backend
    // e.g., POST /api/agents/{agentId}/command with action: "disable_self_healing"
  };

  if (isLoading && !agentHealth) {
    return (
      <div className="flex justify-center items-center h-full text-lg">
        Loading Self-Healing Status...
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader
        title="SELF-HEALING CONSOLE"
        subtitle="Monitor and manage autonomous error detection and remediation across agents."
        actions={
          <div className="flex items-center space-x-2">
            <ShieldCheck className="text-primary" size={20} />
          </div>
        }
      />

      {error && (
        <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      {agentHealth ? (
        <>
          <div className="p-4 bg-card rounded-lg shadow-sm mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-lg font-semibold mb-2 flex items-center"><Cpu className="mr-2" /> Agent Overview</h3>
              <p><strong>Agent ID:</strong> {agentHealth.agent_id || 'N/A'}</p>
              <p><strong>Status:</strong> <Badge variant={agentHealth.status === 'online' ? 'success' : 'destructive'}>{agentHealth.status}</Badge></p>
              <p><strong>OS:</strong> {agentHealth.os || 'N/A'}</p>
              <p><strong>Last Seen:</strong> {agentHealth.last_seen ? new Date(agentHealth.last_seen).toLocaleString() : 'N/A'}</p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2 flex items-center"><Settings className="mr-2" /> Self-Healing Status</h3>
              <p><strong>Self-Healing Enabled:</strong> <Badge variant={agentHealth.self_healing_enabled ? 'success' : 'outline'}>{agentHealth.self_healing_enabled ? 'Yes' : 'No'}</Badge></p>
              <p><strong>SAFE_MODE Active:</strong> <Badge variant={agentHealth.safe_mode_active ? 'warning' : 'outline'}>{agentHealth.safe_mode_active ? 'Yes' : 'No'}</Badge></p>
              <p><strong>Capabilities:</strong> {agentHealth.capabilities ? agentHealth.capabilities.os_type : 'N/A'} (and more...)</p>
              <div className="mt-2">
                <Button variant="outline" size="sm" onClick={() => handleManualOverride('disable_self_healing')}" className="mr-2">Disable Self-Healing</Button>
                <Button variant="outline" size="sm" onClick={() => handleManualOverride('enable_safe_mode')}>Enable SAFE_MODE</Button>
              </div>
            </div>
          </div>

          <div className="p-4 bg-card rounded-lg shadow-sm mb-4">
            <h3 className="text-lg font-semibold mb-2 flex items-center"><AlertCircle className="mr-2" /> Recent Errors & Fixes</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Error Fingerprint</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Root Cause</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentErrors.length > 0 ? (
                  recentErrors.map((err, index) => (
                    <TableRow key={index}>
                      <TableCell>{new Date(err.timestamp).toLocaleString()}</TableCell>
                      <TableCell>{err.fingerprint}</TableCell>
                      <TableCell><Badge variant={err.severity === 'SEV1' ? 'destructive' : err.severity === 'SEV2' ? 'warning' : 'default'}>{err.severity}</Badge></TableCell>
                      <TableCell>{err.root_cause}</TableCell>
                      <TableCell><Badge variant={err.status === 'fixed' ? 'success' : 'destructive'}>{err.status}</Badge></TableCell>
                      <TableCell>
                        <details>
                          <summary>View Details</summary>
                          <pre className="text-xs bg-gray-100 p-2 rounded max-h-40 overflow-y-auto">
                            {JSON.stringify(err.details, null, 2)}
                            {err.fix_attempted && `\n\nFix Attempted: ${err.fix_attempted}\nFix Log: ${err.fix_log}`}
                          </pre>
                        </details>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow><TableCell colSpan={6} className="text-center">No recent errors reported.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          <div className="p-4 bg-card rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-2 flex items-center"><XCircle className="mr-2" /> Manual Actions</h3>
            <div className="flex space-x-4">
              <Button onClick={() => handleManualOverride('trigger_repair')} disabled={isLoading}>Trigger Repair (Not Implemented)</Button>
              <Button onClick={() => handleManualOverride('request_patch')} disabled={isLoading}>Request Patch (Not Implemented)</Button>
              <Button onClick={() => handleManualOverride('initiate_recovery')} disabled={isLoading}>Initiate Recovery (Not Implemented)</Button>
            </div>
          </div>
        </>
      ) : (
        <div className="flex justify-center items-center h-full text-lg text-muted-foreground">
          No agent data available. Please ensure an agent is running and reporting.
        </div>
      )}
    </motion.div>
  );
};

export default SelfHealingConsolePage;
