import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
    Search, 
    Download, 
    Filter, 
    Calendar, 
    ShieldAlert, 
    Cpu, 
    FileText, 
    Terminal, 
    RefreshCw,
    AlertOctagon,
    GitCommit,
    CheckCircle2,
    Database,
    Binary,
    ShieldCheck
} from 'lucide-react';

const ForensicsPage = () => {
    const [selectedAsset, setSelectedAsset] = useState('all');
    const [selectedSeverity, setSelectedSeverity] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [runningJobs, setRunningJobs] = useState([
        { id: 'job-5501', task: 'Live RAM dump extraction', target: 'Ubuntu-Web-01', status: 'In Progress', progress: 68, started: '3m ago' },
        { id: 'job-5502', task: 'Master File Table (MFT) indexing', target: 'Active-Directory-DC', status: 'Pending', progress: 0, started: '10s ago' }
    ]);

    const forensicsTimeline = [
        { 
            time: '2026-05-29T07:12:00Z', 
            asset: 'Ubuntu-Web-01', 
            severity: 'critical', 
            ttpid: 'T1190', 
            title: 'Initial Web Exploit', 
            description: 'Remote Code Execution detected on DMZ Nginx server. Suspicious shell spawned under www-data user context.',
            evidence: 'pcap_capture_stream_009.pcap',
            category: 'Initial Access'
        },
        { 
            time: '2026-05-29T07:15:30Z', 
            asset: 'Ubuntu-Web-01', 
            severity: 'high', 
            ttpid: 'T1059', 
            title: 'Privilege Escalation Exploit', 
            description: 'Local buffer overflow exploit run on sudo permissions. www-data context escalated to root access.',
            evidence: 'bash_history_audit_log.txt',
            category: 'Execution'
        },
        { 
            time: '2026-05-29T07:22:15Z', 
            asset: 'Active-Directory-DC', 
            severity: 'critical', 
            ttpid: 'T1078', 
            title: 'Lateral Movement Trigger', 
            description: 'Compromised admin credentials used to execute remote PowerShell calls to the corporate Domain Controller.',
            evidence: 'event_log_security_4624.evtx',
            category: 'Lateral Movement'
        },
        { 
            time: '2026-05-29T07:38:00Z', 
            asset: 'SQL-DB-02', 
            severity: 'critical', 
            ttpid: 'T1041', 
            title: 'Data Exfiltration Over DNS', 
            description: 'Large-scale compressed DB tables staged and exfiltrated using recursive DNS queries to suspicious external domain.',
            evidence: 'dns_query_vault_901.log',
            category: 'Exfiltration'
        }
    ];

    const evidenceVault = [
        { id: 'art-01', name: 'RAM_Dump_Ubuntu_DMZ.raw', size: '4.2 GB', type: 'Volatile Memory', sha256: '5a28cde10874e...89abf0212', downloaded: true, verified: true },
        { id: 'art-02', name: 'Network_Capture_DNS_Tunnel.pcap', size: '184 MB', type: 'PCAP Flow', sha256: '1a3f01b8e907d...c82ab4409', downloaded: false, verified: true },
        { id: 'art-03', name: 'MFT_Index_DC_Controller.csv', size: '89 MB', type: 'Filesystem Registry', sha256: '9f220de1aa788...bb678c121', downloaded: false, verified: true },
        { id: 'art-04', name: 'Sudo_Exploit_Payload.bin', size: '2 KB', type: 'Malware Sample', sha256: 'e3b0c44298fc1...c149afbf4', downloaded: false, verified: false }
    ];

    const launchForensicJob = (task, target) => {
        setRunningJobs(prev => [
            {
                id: `job-${Math.floor(Math.random() * 9000) + 1000}`,
                task,
                target,
                status: 'Running',
                progress: 10,
                started: 'Just now'
            },
            ...prev
        ]);
    };

    const getSeverityBadge = (sev) => {
        const lower = sev.toLowerCase();
        if (lower === 'critical') return <Badge className="bg-red-500/25 border-red-500/30 text-red-400 font-mono text-[9px]">CRITICAL</Badge>;
        if (lower === 'high') return <Badge className="bg-amber-500/25 border-amber-500/30 text-amber-400 font-mono text-[9px]">HIGH</Badge>;
        return <Badge className="bg-cyan-500/25 border-cyan-500/30 text-cyan-400 font-mono text-[9px]">MEDIUM</Badge>;
    };

    const filteredTimeline = forensicsTimeline.filter(item => {
        const matchesAsset = selectedAsset === 'all' || item.asset === selectedAsset;
        const matchesSeverity = selectedSeverity === 'all' || item.severity === selectedSeverity;
        const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                              item.description.toLowerCase().includes(searchQuery.toLowerCase()) || 
                              item.ttpid.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesAsset && matchesSeverity && matchesSearch;
    });

    return (
        <div className="h-full flex flex-col space-y-6">
            <PageHeader 
                title="FORENSIC COMPOSER & EVIDENCE VAULT"
                subtitle="Live volatile memory dumps, system journal parsing, and timeline reconstruction tools."
                actions={
                    <div className="flex space-x-2">
                        <Button 
                            onClick={() => launchForensicJob('Gather event log traces', 'SQL-DB-02')}
                            className="bg-primary hover:bg-primary/95 text-primary-foreground font-bold text-xs h-9 flex items-center justify-center space-x-2 shadow-[0_0_15px_rgba(139,92,246,0.4)]"
                        >
                            <Cpu className="w-3.5 h-3.5" />
                            <span>LAUNCH DYNAMIC ACQUISITION</span>
                        </Button>
                    </div>
                }
            />

            {/* Quick Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Volatile Artifacts</p>
                            <h3 className="text-2xl font-black font-mono text-white mt-1">4 Collected</h3>
                        </div>
                        <Binary className="w-8 h-8 text-primary opacity-40" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Compromise Lifespans</p>
                            <h3 className="text-2xl font-black font-mono text-red-500 mt-1">26 Mins</h3>
                        </div>
                        <AlertOctagon className="w-8 h-8 text-red-500 opacity-40 animate-pulse" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Forensics Jobs</p>
                            <h3 className="text-2xl font-black font-mono text-amber-500 mt-1">{runningJobs.length} Active</h3>
                        </div>
                        <RefreshCw className="w-8 h-8 text-amber-500 opacity-40" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Custody Integrity</p>
                            <h3 className="text-2xl font-black font-mono text-emerald-400 mt-1">100% Secure</h3>
                        </div>
                        <ShieldCheck className="w-8 h-8 text-emerald-400 opacity-40" />
                    </CardContent>
                </Card>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
                {/* Left Panel: Jobs Tracker & Evidence Vault */}
                <div className="lg:col-span-4 space-y-6 flex flex-col min-h-0">
                    {/* Active Jobs */}
                    <Card className="glass-panel border-primary/20 flex flex-col">
                        <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                            <CardTitle className="text-xs uppercase tracking-widest text-white flex items-center">
                                <RefreshCw className="w-4 h-4 mr-2 text-primary animate-spin-slow" />
                                LIVE VOLATILE ACQUISITION JOBS
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 space-y-4">
                            {runningJobs.map((job) => (
                                <div key={job.id} className="p-3 rounded-lg bg-black border border-white/5 space-y-2">
                                    <div className="flex justify-between items-center text-xs font-mono">
                                        <div>
                                            <span className="text-primary font-bold">{job.task}</span>
                                            <p className="text-[9px] text-muted-foreground mt-0.5">Target: {job.target} • {job.started}</p>
                                        </div>
                                        <Badge className="bg-primary/20 text-primary border-primary/30 text-[8px] animate-pulse">
                                            {job.status.toUpperCase()}
                                        </Badge>
                                    </div>
                                    <div className="w-full bg-[#182030] h-1 rounded-full overflow-hidden">
                                        <motion.div 
                                            className="h-full bg-primary"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${job.progress || 100}%` }}
                                            transition={{ duration: 0.5 }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>

                    {/* Evidence Vault */}
                    <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                        <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                            <CardTitle className="text-xs uppercase tracking-widest text-white flex items-center">
                                <Database className="w-4 h-4 mr-2 text-primary" />
                                CRYPTOGRAPHIC CUSTODY VAULT
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 flex-1 overflow-y-auto custom-scrollbar">
                            <div className="divide-y divide-white/5">
                                {evidenceVault.map((item) => (
                                    <div key={item.id} className="p-3 hover:bg-muted/10 transition-all space-y-1.5 text-xs font-mono">
                                        <div className="flex justify-between items-center">
                                            <span className="font-bold text-white leading-tight truncate block max-w-[200px]">{item.name}</span>
                                            <Badge className={`text-[8px] uppercase ${item.verified ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                                                {item.verified ? 'Verified Hash' : 'Unverified'}
                                            </Badge>
                                        </div>
                                        <p className="text-[10px] text-muted-foreground">{item.type} • {item.size}</p>
                                        <p className="text-[9px] text-muted-foreground truncate max-w-xs block">SHA256: {item.sha256}</p>
                                        <div className="pt-1 flex justify-end">
                                            <Button size="sm" variant="outline" className="h-6 text-[9px] border-white/5 text-white font-mono flex items-center space-x-1 hover:bg-primary/20">
                                                <Download className="w-3 h-3" />
                                                <span>Acquire</span>
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Panel: Reconstructed Attack Timeline */}
                <Card className="lg:col-span-8 glass-panel border-primary/20 overflow-hidden flex flex-col">
                    <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-3">
                            <div>
                                <CardTitle className="text-xs uppercase tracking-widest text-white">RECONSTRUCTED ATTACK TIMELINE</CardTitle>
                                <CardDescription className="text-[10px] text-muted-foreground">Correlated attack progression and multi-stage lateral vectors.</CardDescription>
                            </div>
                            <Button variant="outline" size="sm" className="h-7 text-[10px] border-white/5 text-white font-mono flex items-center space-x-1">
                                <FileText className="w-3.5 h-3.5" />
                                <span>EXPORT FORENSIC REPORT</span>
                            </Button>
                        </div>

                        {/* Search and Filters */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
                            <div className="relative">
                                <Search className="absolute left-2 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
                                <Input 
                                    placeholder="Filter timeline by TTP, text..." 
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="bg-background/50 border-white/5 text-[9px] text-white pl-8 h-8 font-mono"
                                />
                            </div>
                            <Select value={selectedAsset} onValueChange={setSelectedAsset}>
                                <SelectTrigger className="bg-background/50 border-white/5 text-[9px] text-white font-mono h-8">
                                    <SelectValue placeholder="Target Node..." />
                                </SelectTrigger>
                                <SelectContent className="bg-[#0b0e14] border-white/5 text-[9px] text-white font-mono">
                                    <SelectItem value="all" className="focus:bg-primary/20 text-[9px]">All Target Assets</SelectItem>
                                    <SelectItem value="Ubuntu-Web-01" className="focus:bg-primary/20 text-[9px]">Ubuntu-Web-01</SelectItem>
                                    <SelectItem value="Active-Directory-DC" className="focus:bg-primary/20 text-[9px]">Active-Directory-DC</SelectItem>
                                    <SelectItem value="SQL-DB-02" className="focus:bg-primary/20 text-[9px]">SQL-DB-02</SelectItem>
                                </SelectContent>
                            </Select>
                            <Select value={selectedSeverity} onValueChange={setSelectedSeverity}>
                                <SelectTrigger className="bg-background/50 border-white/5 text-[9px] text-white font-mono h-8">
                                    <SelectValue placeholder="Alert Severity..." />
                                </SelectTrigger>
                                <SelectContent className="bg-[#0b0e14] border-white/5 text-[9px] text-white font-mono">
                                    <SelectItem value="all" className="focus:bg-primary/20 text-[9px]">All Severities</SelectItem>
                                    <SelectItem value="critical" className="focus:bg-primary/20 text-[9px]">Critical Only</SelectItem>
                                    <SelectItem value="high" className="focus:bg-primary/20 text-[9px]">High Only</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardHeader>
                    <CardContent className="p-4 flex-1 overflow-y-auto custom-scrollbar">
                        {filteredTimeline.length === 0 ? (
                            <div className="h-44 flex flex-col items-center justify-center text-muted-foreground text-xs italic">
                                <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                                No timeline elements match the selected filter.
                            </div>
                        ) : (
                            <div className="relative pl-6 border-l border-primary/20 space-y-6">
                                {filteredTimeline.map((item, index) => (
                                    <div key={index} className="relative space-y-2">
                                        {/* Timeline Dot */}
                                        <span className="absolute -left-[30px] top-1 bg-background border border-primary w-4.5 h-4.5 rounded-full flex items-center justify-center shadow-lg">
                                            <GitCommit size={10} className="text-primary animate-pulse" />
                                        </span>
                                        
                                        <div className="flex flex-wrap items-center justify-between gap-2">
                                            <div className="flex items-center space-x-2">
                                                <Badge className="bg-primary/20 text-primary border-primary/30 font-mono text-[8px] uppercase">
                                                    {item.category}
                                                </Badge>
                                                <Badge className="bg-muted border-white/5 text-white font-mono text-[8px]">
                                                    MITRE TTP: {item.ttpid}
                                                </Badge>
                                                {getSeverityBadge(item.severity)}
                                            </div>
                                            <span className="text-[9px] font-mono text-muted-foreground">{new Date(item.time).toLocaleString()}</span>
                                        </div>

                                        <h4 className="text-xs font-black tracking-tight text-white">{item.title}</h4>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            {item.description}
                                        </p>
                                        <div className="p-2 rounded bg-black/60 border border-white/5 flex justify-between items-center text-[9px] font-mono text-muted-foreground max-w-lg">
                                            <span>Target Host: <span className="text-white">{item.asset}</span></span>
                                            <span>Custody Artifact: <span className="text-primary font-bold cursor-pointer underline">{item.evidence}</span></span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default ForensicsPage;
