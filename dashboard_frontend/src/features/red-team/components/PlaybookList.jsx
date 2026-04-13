import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlayCircle, FileText, XCircle, Clock } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import StatusChip from '@/components/shared/StatusChip';

const playbookData = [
  {
    id: 'pb-001',
    name: 'Endpoint Compromise Simulation',
    description: 'Simulates a common endpoint compromise scenario to test detection and response capabilities.',
    lastRun: '2023-10-20',
    status: 'completed',
    risk: 'High',
    enabled: true,
  },
  {
    id: 'pb-002',
    name: 'Phishing Attack Vector Test',
    description: 'Tests user susceptibility and email gateway effectiveness against phishing attacks.',
    lastRun: '2023-10-15',
    status: 'failed',
    risk: 'Medium',
    enabled: true,
  },
  {
    id: 'pb-003',
    name: 'Lateral Movement Validation',
    description: 'Verifies defenses against lateral movement techniques within the network.',
    lastRun: '2023-10-01',
    status: 'completed',
    risk: 'High',
    enabled: false,
  },
  {
    id: 'pb-004',
    name: 'Data Exfiltration Test',
    description: 'Attempts to exfiltrate sensitive data to test DLP and egress filtering.',
    lastRun: '2023-09-28',
    status: 'completed',
    risk: 'Critical',
    enabled: true,
  },
];

const PlaybookList = ({ onRunPlaybook, onViewReport }) => {
  const getStatusChip = (status) => {
    switch (status) {
      case 'completed': return <StatusChip status="healthy" className="bg-primary/20 text-primary">COMPLETED</StatusChip>;
      case 'failed': return <StatusChip status="unhealthy" className="bg-destructive/20 text-destructive">FAILED</StatusChip>;
      case 'running': return <StatusChip status="pending" className="bg-secondary/20 text-secondary">RUNNING</StatusChip>;
      default: return <StatusChip status="offline" className="bg-text-secondary/20 text-text-secondary">N/A</StatusChip>;
    }
  };

  return (
    <div className="grid gap-4">
      {playbookData.map((playbook) => (
        <motion.div
          key={playbook.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          whileHover={{ scale: 1.01, boxShadow: "0 0 15px rgba(0, 255, 138, 0.2)" }}
        >
          <Card className="flex flex-col md:flex-row justify-between items-start md:items-center p-4">
            <div className="flex-1 mb-4 md:mb-0">
              <CardTitle className="text-lg text-primary flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                {playbook.name}
              </CardTitle>
              <p className="text-sm text-text-secondary mt-1">{playbook.description}</p>
              <div className="flex items-center text-xs text-muted-foreground mt-2">
                <Clock className="w-3 h-3 mr-1" />
                Last Run: {playbook.lastRun || 'Never'}
                <span className="mx-2">|</span>
                Status: {getStatusChip(playbook.status)}
                <span className="mx-2">|</span>
                Risk: <span className={cn("font-bold ml-1", playbook.risk === 'High' || playbook.risk === 'Critical' ? 'text-destructive' : 'text-primary')}>{playbook.risk.toUpperCase()}</span>
              </div>
            </div>
            <div className="flex flex-col md:flex-row gap-2">
              <Button
                onClick={() => onRunPlaybook(playbook.id)}
                disabled={!playbook.enabled}
                className={cn("bg-primary hover:bg-primary/90 text-primary-foreground", !playbook.enabled && "opacity-50 cursor-not-allowed")}
              >
                <PlayCircle className="w-4 h-4 mr-2" /> RUN
              </Button>
              <Button
                onClick={() => onViewReport(playbook.id)}
                variant="outline"
                className="bg-background hover:bg-accent/20 text-text-primary border-border"
              >
                <FileText className="w-4 h-4 mr-2" /> REPORT
              </Button>
              {!playbook.enabled && (
                <Button variant="destructive" className="hover:bg-destructive/90">
                  <XCircle className="w-4 h-4 mr-2" /> DISABLED
                </Button>
              )}
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
};

export default PlaybookList;
