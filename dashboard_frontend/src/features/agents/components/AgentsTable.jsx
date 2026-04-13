import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowUpDown, Shield } from 'lucide-react';
import StatusChip from '@/components/shared/StatusChip';
import ActionMenu from './ActionMenu';
import AgentModal from './AgentModal';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

// Dummy data for agents
const initialAgents = [
  {
    id: 'agent-123-abc',
    name: 'Endpoint Sentinel Alpha',
    status: 'online',
    version: '1.2.1',
    lastHeartbeat: Date.now(),
    ipAddress: '192.168.1.100',
    cpuLoad: 25,
    certificateValid: true,
    metadata: { os: 'Windows', version: '10 Pro' },
  },
  {
    id: 'agent-456-def',
    name: 'Server Guardian Beta',
    status: 'quarantined',
    version: '1.1.5',
    lastHeartbeat: Date.now() - 3600000, // 1 hour ago
    ipAddress: '10.0.0.50',
    cpuLoad: 70,
    certificateValid: false,
    metadata: { os: 'Linux', distro: 'Ubuntu 20.04' },
  },
  {
    id: 'agent-789-ghi',
    name: 'Perimeter Monitor Gamma',
    status: 'offline',
    version: '1.3.0',
    lastHeartbeat: Date.now() - 7200000, // 2 hours ago
    ipAddress: '172.16.0.1',
    cpuLoad: 0,
    certificateValid: true,
    metadata: { os: 'FreeBSD' },
  },
  {
    id: 'agent-101-jkl',
    name: 'Workstation Defender Delta',
    status: 'online',
    version: '1.2.5',
    lastHeartbeat: Date.now(),
    ipAddress: '192.168.1.101',
    cpuLoad: 15,
    certificateValid: true,
    metadata: { os: 'macOS', version: 'Ventura' },
  },
];

const AgentsTable = () => {
  const [agents, setAgents] = useState(initialAgents);
  const [sortConfig, setSortConfig] = useState({ key: 'lastHeartbeat', direction: 'descending' });
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);

  const sortedAgents = React.useMemo(() => {
    let sortableAgents = [...agents];
    if (sortConfig.key) {
      sortableAgents.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableAgents;
  }, [agents, sortConfig]);

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const handleAction = (agentId, actionType) => {
    // In a real app, this would dispatch to an API
    console.log(`Agent ${agentId} - Action: ${actionType}`);
    setAgents(prevAgents => prevAgents.map(agent => {
        if (agent.id === agentId) {
            if (actionType === 'revoke') return { ...agent, status: 'offline', certificateValid: false };
            if (actionType === 'approve') return { ...agent, status: 'online', certificateValid: true };
            if (actionType === 'quarantine') return { ...agent, status: 'quarantined' };
        }
        return agent;
    }));
  };

  const handleViewDetails = (agentId) => {
    const agent = agents.find(a => a.id === agentId);
    setSelectedAgent(agent);
    setModalOpen(true);
  };

  const columnHeaders = [
    { key: 'name', label: 'Agent Name' },
    { key: 'status', label: 'Status' },
    { key: 'version', label: 'Version' },
    { key: 'lastHeartbeat', label: 'Last Heartbeat' },
    { key: 'ipAddress', label: 'IP Address' },
    { key: 'cpuLoad', label: 'CPU Load' },
    { key: 'certificateValid', label: 'Cert. Valid' },
    { key: 'actions', label: 'Actions', sortable: false },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl overflow-hidden font-mono"
    >
      <Table>
        <TableHeader className="bg-panel-solid border-b border-border">
          <TableRow>
            {columnHeaders.map((header) => (
              <TableHead key={header.key} className="text-primary-foreground">
                {header.sortable !== false ? (
                  <Button
                    variant="ghost"
                    onClick={() => requestSort(header.key)}
                    className="flex items-center text-primary-foreground hover:text-primary"
                  >
                    {header.label}
                    <ArrowUpDown className={cn(
                        "ml-2 h-4 w-4 text-text-secondary transition-transform",
                        sortConfig.key === header.key && sortConfig.direction === 'descending' && "rotate-180",
                        sortConfig.key === header.key && "text-primary"
                    )} />
                  </Button>
                ) : (
                  <span className="p-4 inline-flex">{header.label}</span>
                )}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedAgents.map((agent) => (
            <TableRow key={agent.id} className="border-border hover:bg-accent/10 transition-colors">
              <TableCell className="font-medium flex items-center">
                <Shield className="h-4 w-4 mr-2 text-text-secondary" />
                {agent.name}
              </TableCell>
              <TableCell><StatusChip status={agent.status} /></TableCell>
              <TableCell className="text-text-secondary">{agent.version}</TableCell>
              <TableCell className="text-text-secondary">
                {new Date(agent.lastHeartbeat).toLocaleString()}
              </TableCell>
              <TableCell className="text-text-secondary">{agent.ipAddress}</TableCell>
              <TableCell className="text-text-secondary">{agent.cpuLoad}%</TableCell>
              <TableCell>{agent.certificateValid ? <StatusChip status="healthy" /> : <StatusChip status="unhealthy" />}</TableCell>
              <TableCell>
                <ActionMenu
                  agentId={agent.id}
                  onApprove={() => handleAction(agent.id, 'approve')}
                  onRevoke={() => handleAction(agent.id, 'revoke')}
                  onQuarantine={() => handleAction(agent.id, 'quarantine')}
                  onViewDetails={handleViewDetails}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <AgentModal
        agent={selectedAgent}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </motion.div>
  );
};

export default AgentsTable;
