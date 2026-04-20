import React, { useState, useEffect, useRef } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { BookCopy, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import FormatSwitch from '@/features/log-viewer/components/FormatSwitch';
import ActionBar from '@/features/log-viewer/components/ActionBar';
import LogStreamViewer from '@/features/log-viewer/components/LogStreamViewer';

const mockLogs = [
  '{"timestamp": "2023-10-27T10:00:00Z", "level": "INFO", "message": "User login successful", "user": "admin"}',
  '{"timestamp": "2023-10-27T10:00:05Z", "level": "WARN", "message": "High CPU usage detected", "cpu": "95%"}',
  '{"timestamp": "2023-10-27T10:00:10Z", "level": "ERROR", "message": "Failed to connect to database", "db": "main"}',
  '{"timestamp": "2023-10-27T10:00:15Z", "level": "INFO", "message": "Agent heartbeat received", "agentId": "agent-alpha"}',
  '2023-10-27 10:00:20 - CRITICAL: Unauthorized access attempt detected from 192.168.1.1',
  '{"timestamp": "2023-10-27T10:00:25Z", "level": "DEBUG", "message": "Processing request", "requestId": "xyz123"}',
  '2023-10-27 10:00:30 - INFO: System backup initiated.',
  '{"timestamp": "2023-10-27T10:00:35Z", "level": "WARN", "message": "Disk space low", "freeSpace": "10%"}',
  '{"timestamp": "2023-10-27T10:00:40Z", "level": "INFO", "message": "Configuration updated", "configItem": "network_settings"}',
  '2023-10-27 10:00:45 - ERROR: Malicious payload detected and quarantined.',
];

const LogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [format, setFormat] = useState('formatted'); // 'raw' or 'formatted'
  const logIndexRef = useRef(0);

  useEffect(() => {
    const interval = setInterval(() => {
      if (logIndexRef.current < mockLogs.length) {
        setLogs((prevLogs) => [...prevLogs, mockLogs[logIndexRef.current]]);
        logIndexRef.current++;
      } else {
        // Loop back for continuous simulation
        logIndexRef.current = 0;
        // Optionally clear logs to simulate a new session or continuous stream
        // setLogs([]); 
      }
    }, 1500); // Add a new log every 1.5 seconds

    return () => clearInterval(interval);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(logs.join('\n'));
    alert('Logs copied to clipboard!'); // Replace with a more elegant toast
  };

  const handleExport = () => {
    const blob = new Blob([logs.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `phantomnet_logs_${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setLogs([]);
    logIndexRef.current = 0; // Reset index to restart stream
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="STRUCTURED LOG VIEWER"
        subtitle="Analyze and filter raw system and event logs."
        actions={
            <div className="flex items-center space-x-4">
                <FormatSwitch format={format} onFormatChange={setFormat} />
                <Button className="bg-secondary hover:bg-secondary/90 text-secondary-foreground">
                    <Search className="w-4 h-4 mr-2" />ADVANCED SEARCH
                </Button>
            </div>
        }
      />
      
      <ActionBar onCopy={handleCopy} onExport={handleExport} onClear={handleClear} />

      <div className="flex-1 min-h-0 mt-4">
        <LogStreamViewer logs={logs} format={format} />
      </div>
    </motion.div>
  );
};

export default LogViewer;
