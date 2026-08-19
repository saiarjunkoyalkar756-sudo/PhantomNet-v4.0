import React, { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
    Zap,
    Clock,
    CheckCircle2,
    AlertTriangle,
    Play,
    History,
    ShieldAlert,
    ShieldCheck,
    Cpu,
    ArrowRight,
    RefreshCw,
    ToggleLeft,
    ToggleRight,
    Terminal,
    UserCheck,
    Search,
    AlertCircle
} from 'lucide-react';
import soarService from '../services/soar.service';

const MotionDiv = motion.div;

const FALLBACK_PLAYBOOKS = [
    { id: 'pb-001', name: 'Ransomware Containment', description: 'Automatically disconnects the endpoint from network and takes a secure VSS shadow copy upon sensing massive write system spikes.', type: 'Active Isolation', severity: 'Critical', active: true },
    { id: 'pb-002', name: 'C2 Threat IP Blocking', description: 'Injects dynamic iptables/firewall rules to block outgoing requests to flagged command & control servers.', type: 'Network Containment', severity: 'High', active: true },
    { id: 'pb-003', name: 'Phishing Token Revocation', description: 'Terminates active web sessions and rotates authorization tokens of users demonstrating aberrant geographic jumps.', type: 'Session Revocation', severity: 'Medium', active: false },
    { id: 'pb-004', name: 'AI Honeypot Redirection', description: 'Gracefully redirects suspicious port scanning activities to a synthetic decoy network container.', type: 'Intrusion Deception', severity: 'Low', active: true },
    { id: 'pb-005', name: 'LDAP Brute Force Mitigation', description: 'Applies rigorous exponential login delays on specific directory service targets after recurrent failures.', type: 'Identity Hardening', severity: 'High', active: true },
];

const SOARPage = () => {
    const [view, setView] = useState('orchestration'); // 'orchestration' | 'library' | 'history'
    const [playbooks, setPlaybooks] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');

    // Interactive states
    const [pendingApprovals, setPendingApprovals] = useState([
        { id: 'app-001', playbook: 'Ransomware Containment', step: 'Isolate Host: DC-01', risk: 'Critical', requestedAt: '2m ago', target: '192.168.10.15' },
        { id: 'app-002', playbook: 'Data Exfiltration Protection', step: 'Block Outbound IP: 45.33.21.11', risk: 'High', requestedAt: '5m ago', target: '45.33.21.11' },
        { id: 'app-003', playbook: 'Credential Rotation Trigger', step: 'Rotate Administrator AD Creds', risk: 'Medium', requestedAt: '12m ago', target: 'AD-Controller' }
    ]);

    const [activeExecutions, setActiveExecutions] = useState([
        { id: 'run-881', name: 'Brute Force Mitigation', status: 'Running', step: 'Rate Limiting User account: j.doe', progress: 65, startTime: '1m ago' },
        { id: 'run-882', name: 'Suspicious DLL Detection', status: 'In Progress', step: 'Awaiting Automated Sandbox Verdict', progress: 30, startTime: '3m ago' },
        { id: 'run-883', name: 'Lateral Movement Isolation', status: 'Analyzing', step: 'Tracing RPC calls from WebServer', progress: 90, startTime: 'Just now' }
    ]);

    const [recentRuns, setRecentRuns] = useState([
        { id: 'run-101', playbook: 'Malware Auto-Quarantine', target: 'endpoint-ubuntu-02', status: 'success', time: '10 mins ago', duration: '12s' },
        { id: 'run-102', playbook: 'C2 IP Address Block', target: 'firewall-perimeter', status: 'success', time: '45 mins ago', duration: '2s' },
        { id: 'run-103', playbook: 'Honeypot Decoy Engagement', target: 'subnet-dmz-honeypot', status: 'success', time: '2 hours ago', duration: '1.4s' },
        { id: 'run-104', playbook: 'SQL Injection Block', target: 'api-gateway', status: 'failed', time: '4 hours ago', duration: '5.8s', error: 'Gateway timeout' }
    ]);

    const [blockedIps, setBlockedIps] = useState([
        { ip: '185.220.101.5', reason: 'Tor Exit Node / C2 Activity', blockedAt: '2026-05-29 06:12', severity: 'Critical' },
        { ip: '91.240.118.4', reason: 'SSH Brute Force Scans', blockedAt: '2026-05-29 07:05', severity: 'High' },
        { ip: '103.88.22.141', reason: 'API Ingestion Flooding', blockedAt: '2026-05-29 07:44', severity: 'Medium' }
    ]);

    // Manual playbook execution input form
    const [selectedPlaybookId, setSelectedPlaybookId] = useState('');
    const [targetInput, setTargetInput] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [executionOutput, setExecutionOutput] = useState('');

    const fetchPlaybooks = useCallback(async () => {
        try {
            const response = await soarService.getPlaybooks();
            const list = response.data?.data || response.data || response;
            setPlaybooks(Array.isArray(list) ? list : FALLBACK_PLAYBOOKS);
        } catch (err) {
            console.warn("Failed to fetch SOAR playbooks from API, using fallback data:", err);
            setPlaybooks(FALLBACK_PLAYBOOKS);
        }
    }, []);

    useEffect(() => {
        let cancelled = false;
        queueMicrotask(() => {
            if (!cancelled) {
                void fetchPlaybooks();
            }
        });
        return () => {
            cancelled = true;
        };
    }, [fetchPlaybooks]);

    const handleApprove = (id) => {
        const approved = pendingApprovals.find(x => x.id === id);
        // Simulate adding to active executions
        if (approved) {
            setActiveExecutions(prev => [
                {
                    id: `run-${Math.floor(Math.random() * 900) + 100}`,
                    name: approved.playbook,
                    status: 'Running',
                    step: approved.step.replace('Isolate', 'Isolating').replace('Block', 'Blocking').replace('Rotate', 'Rotating'),
                    progress: 10,
                    startTime: 'Just now'
                },
                ...prev
            ]);
        }
        setPendingApprovals(prev => prev.filter(req => req.id !== id));
    };

    const handleReject = (id) => {
        setPendingApprovals(prev => prev.filter(req => req.id !== id));
    };

    const handleTriggerPlaybook = async (e) => {
        e.preventDefault();
        if (!selectedPlaybookId || !targetInput) return;

        setIsSubmitting(true);
        setExecutionOutput("Initializing orchestration pipeline...\nResolving node credentials...\nConnecting to target node...\n");

        setTimeout(() => {
            const p = playbooks.find(x => x.id === selectedPlaybookId) || FALLBACK_PLAYBOOKS.find(x => x.id === selectedPlaybookId);
            setExecutionOutput(prev => prev + `[+] Playbook [${p?.name}] triggered successfully against target: ${targetInput}.\n[+] Command sequence initiated.\n[+] Countermeasures deployed.\n[+] Execution logged to Immutable Blockchain Ledger.\n[SUCCESS] Node isolated and stabilized.`);

            // Add to active executions
            setActiveExecutions(prev => [
                {
                    id: `run-${Math.floor(Math.random() * 900) + 100}`,
                    name: p?.name || 'Manual Mitigation',
                    status: 'Completed',
                    step: 'Execution completed',
                    progress: 100,
                    startTime: 'Just now'
                },
                ...prev
            ]);

            // Add to recent runs
            setRecentRuns(prev => [
                {
                    id: `run-${Math.floor(Math.random() * 900) + 100}`,
                    playbook: p?.name || 'Manual Mitigation',
                    target: targetInput,
                    status: 'success',
                    time: 'Just now',
                    duration: '2.5s'
                },
                ...prev
            ]);

            setIsSubmitting(false);
            setTargetInput('');
        }, 2000);
    };

    const handleUnblockIp = (ip) => {
        setBlockedIps(prev => prev.filter(x => x.ip !== ip));
    };

    const filteredPlaybooks = playbooks.filter(p =>
        p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="h-full flex flex-col space-y-6">
            <PageHeader
                title="SOAR COMMAND CENTER"
                subtitle="High-density orchestrator automating active defense, threat mitigation, and node isolation."
                actions={
                    <div className="flex bg-muted/40 p-1 rounded-lg border border-white/5">
                        <button
                            onClick={() => setView('orchestration')}
                            className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${view === 'orchestration' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            ORCHESTRATION
                        </button>
                        <button
                            onClick={() => setView('library')}
                            className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${view === 'library' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            PLAYBOOKS ({playbooks.length || FALLBACK_PLAYBOOKS.length})
                        </button>
                        <button
                            onClick={() => setView('history')}
                            className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${view === 'history' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            HISTORY
                        </button>
                    </div>
                }
            />

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Orchestration Rate</p>
                            <h3 className="text-2xl font-black font-mono text-glow-primary text-primary mt-1">94.8%</h3>
                        </div>
                        <Zap className="w-8 h-8 text-primary opacity-40 animate-pulse" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Mean Time To Contain</p>
                            <h3 className="text-2xl font-black font-mono text-emerald-400 mt-1">4.2 Secs</h3>
                        </div>
                        <Clock className="w-8 h-8 text-emerald-400 opacity-40" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Human Hours Saved</p>
                            <h3 className="text-2xl font-black font-mono text-cyan-400 mt-1">391 Hours</h3>
                        </div>
                        <UserCheck className="w-8 h-8 text-cyan-400 opacity-40" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Blockchain Ledgers</p>
                            <h3 className="text-2xl font-black font-mono text-purple-400 mt-1">Verified</h3>
                        </div>
                        <ShieldCheck className="w-8 h-8 text-purple-400 opacity-40" />
                    </CardContent>
                </Card>
            </div>

            {view === 'orchestration' && (
                <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
                    {/* Left Panel: Approvals & Active Flows */}
                    <div className="lg:col-span-8 space-y-6 flex flex-col min-h-0">
                        {/* HITL Approvals */}
                        <Card className="glass-panel border-red-500/25 relative overflow-hidden flex flex-col">
                            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                                <ShieldAlert size={140} />
                            </div>
                            <CardHeader className="pb-3 border-b border-white/5 bg-red-950/10">
                                <CardTitle className="text-xs uppercase tracking-widest flex items-center text-red-400">
                                    <AlertCircle className="w-4 h-4 mr-2 animate-bounce" />
                                    HUMAN-IN-THE-LOOP AUTHORIZATIONS
                                    <Badge className="ml-3 bg-red-500/20 text-red-300 border-red-500/30 text-[9px] font-mono">
                                        {pendingApprovals.length} PENDING
                                    </Badge>
                                </CardTitle>
                                <CardDescription className="text-[10px] text-muted-foreground">
                                    The following countermeasure execution sequences require active administrator overrides.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-3">
                                <AnimatePresence>
                                    {pendingApprovals.length === 0 ? (
                                        <MotionDiv
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            className="h-28 flex flex-col items-center justify-center text-muted-foreground text-xs italic"
                                        >
                                            <ShieldCheck className="w-8 h-8 text-emerald-400 mb-2" />
                                            No pending human authorisations. Automated flows running autonomously.
                                        </MotionDiv>
                                    ) : (
                                        pendingApprovals.map((req) => (
                                            <MotionDiv
                                                key={req.id}
                                                initial={{ x: -20, opacity: 0 }}
                                                animate={{ x: 0, opacity: 1 }}
                                                exit={{ x: 20, opacity: 0 }}
                                                className="p-3.5 rounded-lg bg-red-950/5 border border-red-900/20 flex items-center justify-between group hover:border-red-900/50 transition-all shadow-inner"
                                            >
                                                <div className="space-y-1">
                                                    <div className="flex items-center space-x-2">
                                                        <Badge variant="destructive" className="bg-red-500/25 border-red-500/30 font-mono text-[9px]">
                                                            {req.risk}
                                                        </Badge>
                                                        <h5 className="text-xs font-black tracking-tight text-white">{req.playbook}</h5>
                                                    </div>
                                                    <p className="text-[10px] text-muted-foreground font-mono">
                                                        Target Node: <span className="text-white">{req.target}</span> • Action: <span className="text-white">{req.step}</span>
                                                    </p>
                                                    <p className="text-[8px] text-muted-foreground">{req.requestedAt}</p>
                                                </div>
                                                <div className="flex space-x-2">
                                                    <Button
                                                        size="sm"
                                                        onClick={() => handleReject(req.id)}
                                                        className="h-7 bg-red-950/40 hover:bg-red-950 text-red-300 border border-red-900/30 text-[10px] font-bold px-3 transition-all"
                                                    >
                                                        DENY
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        onClick={() => handleApprove(req.id)}
                                                        className="h-7 bg-primary hover:bg-primary/95 text-primary-foreground text-[10px] font-bold px-3 shadow-[0_0_10px_rgba(139,92,246,0.3)] transition-all"
                                                    >
                                                        AUTHORIZE
                                                    </Button>
                                                </div>
                                            </MotionDiv>
                                        ))
                                    )}
                                </AnimatePresence>
                            </CardContent>
                        </Card>

                        {/* Active Execution Grid */}
                        <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                            <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                                <CardTitle className="text-xs uppercase tracking-widest flex items-center text-white">
                                    <Cpu className="w-4 h-4 mr-2 text-primary animate-pulse" />
                                    ACTIVE PLAYBOOK ORCHESTRATION PIPELINES
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-4">
                                {activeExecutions.map((pb) => (
                                    <div key={pb.id} className="p-3.5 rounded-lg bg-[#0d121c] border border-white/5 space-y-2">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <div className="flex items-center space-x-2">
                                                    <span className="text-[10px] font-mono text-muted-foreground">[{pb.id}]</span>
                                                    <h4 className="text-xs font-black tracking-tight text-white">{pb.name}</h4>
                                                </div>
                                                <p className="text-[10px] text-muted-foreground uppercase flex items-center font-mono mt-0.5">
                                                    <Clock className="w-3 h-3 mr-1" /> {pb.step}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-[9px] font-mono text-primary animate-pulse uppercase">{pb.status} ({pb.progress}%)</span>
                                                <p className="text-[8px] text-muted-foreground font-mono mt-0.5">started {pb.startTime}</p>
                                            </div>
                                        </div>
                                        <div className="w-full bg-[#182030] h-1 rounded-full overflow-hidden">
                                            <MotionDiv
                                                className="h-full bg-primary shadow-[0_0_12px_rgba(139,92,246,0.8)]"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${pb.progress}%` }}
                                                transition={{ duration: 1.5 }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Right Panel: Playbook Trigger Form & Blocked IPs */}
                    <div className="lg:col-span-4 space-y-6 flex flex-col min-h-0">
                        {/* Playbook Launcher */}
                        <Card className="glass-panel border-primary/20">
                            <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                                <CardTitle className="text-xs uppercase tracking-widest flex items-center text-white">
                                    <Play className="w-4 h-4 mr-2 text-primary" />
                                    MANUAL PLAYBOOK LAUNCHER
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-4">
                                <form onSubmit={handleTriggerPlaybook} className="space-y-4">
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] uppercase font-mono tracking-wider text-muted-foreground">Select Mitigation Playbook</label>
                                        <Select value={selectedPlaybookId} onValueChange={setSelectedPlaybookId} required>
                                            <SelectTrigger className="bg-background/50 border-white/5 text-xs text-white">
                                                <SelectValue placeholder="Choose action..." />
                                            </SelectTrigger>
                                            <SelectContent className="bg-[#0b0e14] border-white/5 text-xs text-white">
                                                {(playbooks.length ? playbooks : FALLBACK_PLAYBOOKS).map(p => (
                                                    <SelectItem key={p.id} value={p.id} className="focus:bg-primary/20 text-xs">
                                                        {p.name}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] uppercase font-mono tracking-wider text-muted-foreground">Target IP / Asset ID</label>
                                        <Input
                                            placeholder="e.g. 192.168.1.100"
                                            value={targetInput}
                                            onChange={(e) => setTargetInput(e.target.value)}
                                            className="bg-background/50 border-white/5 text-xs text-white font-mono h-9"
                                            required
                                        />
                                    </div>
                                    <Button
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-bold text-xs h-9 flex items-center justify-center space-x-2"
                                    >
                                        {isSubmitting ? (
                                            <>
                                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                                <span>EXECUTING STACK...</span>
                                            </>
                                        ) : (
                                            <>
                                                <Zap className="w-3.5 h-3.5" />
                                                <span>DEPLOY MITIGATION</span>
                                            </>
                                        )}
                                    </Button>
                                </form>

                                {executionOutput && (
                                    <div className="mt-4 p-3 rounded-lg bg-black border border-white/5 flex flex-col">
                                        <div className="flex justify-between items-center mb-1 text-[9px] font-mono text-muted-foreground uppercase">
                                            <span className="flex items-center"><Terminal className="w-3 h-3 mr-1 text-primary" /> Console Stream</span>
                                            <span className="text-emerald-400">active</span>
                                        </div>
                                        <pre className="text-[9px] font-mono leading-relaxed text-glow-primary text-primary overflow-x-auto whitespace-pre-wrap">
                                            {executionOutput}
                                        </pre>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Perimeter IP Blocks */}
                        <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                            <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                                <CardTitle className="text-xs uppercase tracking-widest flex items-center text-white">
                                    <ShieldAlert className="w-4 h-4 mr-2 text-red-400" />
                                    ACTIVE FIREWALL IP PERIMETER BLOCKS
                                    <Badge className="ml-2 bg-red-500/10 border-red-500/20 text-red-400 text-[9px] font-mono">
                                        {blockedIps.length}
                                    </Badge>
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-0 flex-1 overflow-y-auto custom-scrollbar">
                                <div className="divide-y divide-white/5">
                                    {blockedIps.map((block) => (
                                        <div key={block.ip} className="p-3 hover:bg-muted/15 transition-all flex items-center justify-between">
                                            <div>
                                                <p className="text-xs font-bold font-mono text-white">{block.ip}</p>
                                                <p className="text-[10px] text-muted-foreground font-mono">{block.reason}</p>
                                                <p className="text-[8px] text-muted-foreground mt-0.5">blocked: {block.blockedAt}</p>
                                            </div>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => handleUnblockIp(block.ip)}
                                                className="h-6 border-emerald-500/20 hover:border-emerald-500/50 hover:bg-emerald-500/10 text-emerald-400 text-[9px] font-bold px-2"
                                            >
                                                UNBAN
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            )}

            {view === 'library' && (
                <div className="flex-1 space-y-4">
                    {/* Search Controls */}
                    <Card className="glass-panel border-primary/20 p-4">
                        <div className="flex items-center space-x-3">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search automation playbooks by name, vector, TTPs..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="bg-background/50 border-white/5 text-xs text-white pl-9 h-9"
                                />
                            </div>
                            <Button className="bg-primary hover:bg-primary/95 text-xs h-9">
                                CREATE PLAYBOOK
                            </Button>
                        </div>
                    </Card>

                    {/* Grid List */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {(searchTerm ? filteredPlaybooks : playbooks.length ? playbooks : FALLBACK_PLAYBOOKS).map((p) => (
                            <Card key={p.id} className="glass-panel border-primary/15 hover:border-primary/45 transition-all flex flex-col">
                                <CardHeader className="pb-3 border-b border-white/5 bg-muted/10 flex flex-row justify-between items-start">
                                    <div>
                                        <div className="flex items-center space-x-2">
                                            <Badge className="bg-primary/20 border-primary/30 text-primary-foreground text-[8px] font-mono uppercase">
                                                {p.type || 'Mitigation'}
                                            </Badge>
                                            <Badge className={
                                                p.severity === 'Critical' ? 'bg-red-500/25 border-red-500/30 text-red-300' :
                                                p.severity === 'High' ? 'bg-amber-500/25 border-amber-500/30 text-amber-300' :
                                                'bg-cyan-500/25 border-cyan-500/30 text-cyan-300'
                                            }>
                                                {p.severity || 'Medium'}
                                            </Badge>
                                        </div>
                                        <CardTitle className="text-sm font-black tracking-tight text-white mt-1.5">{p.name}</CardTitle>
                                    </div>
                                    <div className="flex items-center">
                                        {p.active ? (
                                            <ToggleRight className="w-6 h-6 text-primary cursor-pointer" />
                                        ) : (
                                            <ToggleLeft className="w-6 h-6 text-muted-foreground cursor-pointer" />
                                        )}
                                    </div>
                                </CardHeader>
                                <CardContent className="p-4 flex-1 flex flex-col justify-between">
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        {p.description}
                                    </p>
                                    <div className="flex justify-between items-center mt-4 pt-3 border-t border-white/5 text-[9px] font-mono text-muted-foreground">
                                        <span>SYSTEM ID: {p.id}</span>
                                        <span className="flex items-center text-primary font-bold">
                                            EDIT RULES <ArrowRight className="w-3 h-3 ml-1" />
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {view === 'history' && (
                <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                    <CardHeader className="pb-3 border-b border-white/5 bg-muted/10 flex flex-row justify-between items-center">
                        <div>
                            <CardTitle className="text-xs uppercase tracking-widest text-white">HISTORICAL SOAR COUNTERMEASURE LOGS</CardTitle>
                            <CardDescription className="text-[10px] text-muted-foreground">Audit logs of automated response execution outcomes recorded to the blockchain ledger.</CardDescription>
                        </div>
                        <Button variant="outline" size="sm" onClick={fetchPlaybooks} className="h-7 text-[10px] border-white/5 text-white font-mono">
                            <RefreshCw className="w-3 h-3 mr-1" /> SYNC LEDGER
                        </Button>
                    </CardHeader>
                    <CardContent className="p-0 flex-1 overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse text-xs">
                            <thead>
                                <tr className="border-b border-white/5 bg-muted/20 text-muted-foreground text-[10px] font-mono uppercase tracking-wider">
                                    <th className="p-3">Run ID</th>
                                    <th className="p-3">Playbook Action</th>
                                    <th className="p-3">Target Endpoint</th>
                                    <th className="p-3">Result Status</th>
                                    <th className="p-3">Execution Time</th>
                                    <th className="p-3 text-right">Duration</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5 text-white">
                                {recentRuns.map((run) => (
                                    <tr key={run.id} className="hover:bg-muted/10 transition-colors">
                                        <td className="p-3 font-mono text-muted-foreground text-[10px]">[{run.id}]</td>
                                        <td className="p-3 font-bold">{run.playbook}</td>
                                        <td className="p-3 font-mono text-muted-foreground">{run.target}</td>
                                        <td className="p-3">
                                            <Badge className={
                                                run.status === 'success' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                                'bg-red-500/20 text-red-400 border-red-500/30'
                                            }>
                                                {run.status === 'success' ? 'SUCCESS' : 'FAILED'}
                                            </Badge>
                                            {run.error && <span className="text-[9px] text-red-400 font-mono ml-2">({run.error})</span>}
                                        </td>
                                        <td className="p-3 text-muted-foreground">{run.time}</td>
                                        <td className="p-3 text-right font-mono text-muted-foreground">{run.duration}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default SOARPage;
