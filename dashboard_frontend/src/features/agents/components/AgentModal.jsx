import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Shield, Cpu, Wifi, Calendar, CheckCircle, XCircle, Info } from 'lucide-react';
import StatusChip from '@/components/shared/StatusChip';
import { cn } from '@/lib/utils';

const AgentModal = ({ agent, isOpen, onClose }) => {
  if (!agent) return null;

  const getStatusChip = (status) => {
    if (status === 'online') return <StatusChip status="online" />;
    if (status === 'offline') return <StatusChip status="offline" />;
    if (status === 'quarantined') return <StatusChip status="quarantined" />;
    return <StatusChip status="unknown" />;
  };

  const getCertStatusChip = (isValid) => {
    if (isValid) return <StatusChip status="healthy" className="bg-green-700/20 text-green-400">VALID</StatusChip>;
    return <StatusChip status="unhealthy" className="bg-red-700/20 text-destructive">EXPIRED</StatusChip>;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-panel-solid border-border text-text-primary font-mono">
        <DialogHeader>
          <DialogTitle className="flex items-center text-primary text-xl">
            <Shield className="w-6 h-6 mr-2" />
            AGENT DETAILS: {agent.name.toUpperCase()}
          </DialogTitle>
          <DialogDescription className="text-text-secondary text-sm">
            Detailed information and actions for agent <span className="text-primary">{agent.id}</span>.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">ID:</p>
            <p className="col-span-2 text-text-primary break-all">{agent.id}</p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Status:</p>
            <div className="col-span-2">{getStatusChip(agent.status)}</div>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Version:</p>
            <p className="col-span-2 text-text-primary">{agent.version}</p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Last Heartbeat:</p>
            <p className="col-span-2 text-text-primary flex items-center">
                <Calendar className="w-4 h-4 mr-2" />
                {new Date(agent.lastHeartbeat).toLocaleString()}
            </p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">IP Address:</p>
            <p className="col-span-2 text-text-primary flex items-center">
                <Wifi className="w-4 h-4 mr-2" />
                {agent.ipAddress}
            </p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">CPU Load:</p>
            <p className="col-span-2 text-text-primary flex items-center">
                <Cpu className="w-4 h-4 mr-2" />
                {agent.cpuLoad}%
            </p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Cert. Valid:</p>
            <div className="col-span-2">{getCertStatusChip(agent.certificateValid)}</div>
          </div>
          {agent.metadata && (
            <div>
              <p className="text-muted-foreground mb-2">Metadata:</p>
              <pre className="bg-background border border-border p-2 rounded-md text-xs overflow-auto">
                {JSON.stringify(agent.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AgentModal;
