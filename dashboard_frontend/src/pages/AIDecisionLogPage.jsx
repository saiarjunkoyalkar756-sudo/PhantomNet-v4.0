import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Brain, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'react-toastify';

const AIDecisionLogPage = () => {
  const [decisionLogs, setDecisionLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAIDecisionLogs();
    const interval = setInterval(fetchAIDecisionLogs, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAIDecisionLogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // This is a placeholder for fetching AI decision logs from the backend.
      // The backend needs an endpoint like /ai/decision_logs or similar.
      // For now, we'll simulate some data.
      const response = await fetch('/api/ai/decision_logs'); 
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch AI decision logs');
      
      const data = await response.json();
      setDecisionLogs(data.decision_logs || []);

    } catch (err) {
      console.error("Error fetching AI decision logs:", err);
      setError(err.message);
      toast.error(`Error fetching AI decision logs: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && decisionLogs.length === 0) {
    return (
      <div className="flex justify-center items-center h-full text-lg">
        Loading AI Decision Logs...
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
        title="AI DECISION LOG"
        subtitle="Review autonomous decisions made by the PhantomNet AI agents."
        actions={
          <div className="flex items-center space-x-2">
            <Brain className="text-primary" size={20} />
          </div>
        }
      />

      {error && (
        <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="p-4 bg-card rounded-lg shadow-sm mb-4 flex-1 min-h-0">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><FileText className="mr-2" /> Decision History</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Agent ID</TableHead>
              <TableHead>Decision Type</TableHead>
              <TableHead>Outcome</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {decisionLogs.length > 0 ? (
              decisionLogs.map((log, index) => (
                <TableRow key={index}>
                  <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{log.agent_id}</TableCell>
                  <TableCell>{log.decision_type}</TableCell>
                  <TableCell>
                    <Badge variant={log.outcome === 'SUCCESS' ? 'success' : 'destructive'}>
                      {log.outcome}
                    </Badge>
                  </TableCell>
                  <TableCell>{log.confidence ? `${(log.confidence * 100).toFixed(1)}%` : 'N/A'}</TableCell>
                  <TableCell>
                    <details>
                      <summary>View Details</summary>
                      <pre className="text-xs bg-gray-100 p-2 rounded max-h-40 overflow-y-auto">
                        {JSON.stringify(log.details, null, 2)}
                        {log.execution_trace && `\n\nExecution Trace: ${log.execution_trace}`}
                      </pre>
                    </details>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow><TableCell colSpan={6} className="text-center">No AI decision logs found.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </motion.div>
  );
};

export default AIDecisionLogPage;
