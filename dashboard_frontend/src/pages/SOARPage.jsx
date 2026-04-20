import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
    Zap, 
    Clock, 
    CheckCircle2, 
    AlertCircle, 
    Play, 
    History, 
    ShieldCheck,
    Cpu,
    ArrowRight
} from 'lucide-react';

const SOARPage = () => {
    const [view, setView] = useState('active'); // 'active' or 'library'

    const pendingApprovals = [
        { id: 'app-001', playbook: 'Ransomware Containment', step: 'Isolate Host: DC-01', risk: 'Critical', requestedAt: '2m ago' },
        { id: 'app-002', playbook: 'Data Exfiltration Protection', step: 'Block Outbound IP: 45.x.x.x', risk: 'High', requestedAt: '5m ago' },
    ];

    const activePlaybooks = [
        { id: 'p1', name: 'Brute Force Mitigation', status: 'Running', step: 'Rate Limiting Account', progress: 65 },
        { id: 'p2', name: 'Suspicious DLL Detection', status: 'Waiting', step: 'Awaiting Sandbox Analysis', progress: 30 },
    ];

    return (
        <div className="h-full flex flex-col space-y-6">
            <PageHeader 
                title="SOAR MISSION CONTROL"
                subtitle="Security Orchestration, Automation, and Response Orchestrator."
                actions={
                    <div className="flex bg-muted/50 p-1 rounded-lg border border-border">
                        <button 
                            onClick={() => setView('active')}
                            className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${view === 'active' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            ORCHESTRATION
                        </button>
                        <button 
                            onClick={() => setView('library')}
                            className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${view === 'library' ? 'bg-primary text-primary-foreground shadow-lg' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            PLAYBOOK LIBRARY
                        </button>
                    </div>
                }
            />

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
                {/* Left Column: Active State */}
                <div className="lg:col-span-8 space-y-6 flex flex-col min-h-0">
                    {/* Live Execution Status */}
                    <Card className="glass-panel border-primary/20">
                         <CardHeader className="pb-2">
                             <CardTitle className="text-xs uppercase tracking-widest flex items-center">
                                <Cpu className="w-4 h-4 mr-2 text-primary" />
                                ACTIVE AUTOMATION FLOWS
                             </CardTitle>
                         </CardHeader>
                         <CardContent className="space-y-4">
                            {activePlaybooks.map(pb => (
                                <div key={pb.id} className="p-4 rounded-lg bg-background/50 border border-border/50 space-y-3">
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <h4 className="text-sm font-bold text-foreground">{pb.name}</h4>
                                            <p className="text-[10px] text-muted-foreground uppercase flex items-center">
                                                <Clock className="w-3 h-3 mr-1" /> {pb.step}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-[10px] font-mono text-primary animate-pulse">{pb.status}</span>
                                        </div>
                                    </div>
                                    <div className="w-full bg-muted h-1 rounded-full overflow-hidden">
                                        <motion.div 
                                            className="h-full bg-primary shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${pb.progress}%` }}
                                            transition={{ duration: 1.5, repeat: Infinity, repeatType: 'reverse' }}
                                        />
                                    </div>
                                </div>
                            ))}
                         </CardContent>
                    </Card>

                    {/* Pending Approvals (HITL) */}
                    <Card className="flex-1 glass-panel border-destructive/20 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                            <ShieldCheck size={120} />
                        </div>
                        <CardHeader>
                             <CardTitle className="text-xs uppercase tracking-widest flex items-center text-destructive">
                                <AlertCircle className="w-4 h-4 mr-2" />
                                HUMAN-IN-THE-LOOP APPROVALS
                                <span className="ml-2 px-1.5 py-0.5 rounded bg-destructive text-destructive-foreground text-[8px]">{pendingApprovals.length} PENDING</span>
                             </CardTitle>
                         </CardHeader>
                         <CardContent className="space-y-3 custom-scrollbar overflow-y-auto">
                            <AnimatePresence>
                                {pendingApprovals.map((req, idx) => (
                                    <motion.div 
                                        key={idx}
                                        initial={{ x: -20, opacity: 0 }}
                                        animate={{ x: 0, opacity: 1 }}
                                        exit={{ x: 20, opacity: 0 }}
                                        className="p-4 rounded-lg bg-destructive/5 border border-destructive/20 flex items-center justify-between group hover:border-destructive/40 transition-all shadow-inner"
                                    >
                                        <div className="space-y-1">
                                            <div className="flex items-center space-x-2">
                                                <span className="text-xs font-bold font-mono tracking-tighter">[{req.risk}]</span>
                                                <h5 className="text-sm font-bold">{req.playbook}</h5>
                                            </div>
                                            <p className="text-[10px] text-muted-foreground">{req.step} • {req.requestedAt}</p>
                                        </div>
                                        <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button size="sm" className="h-8 bg-destructive hover:bg-destructive/90 text-xs px-4">REJECT</Button>
                                            <Button size="sm" className="h-8 bg-primary hover:bg-primary/90 text-xs px-4">APPROVE</Button>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                         </CardContent>
                    </Card>
                </div>

                {/* Right Column: Library / History */}
                <div className="lg:col-span-4 flex flex-col min-h-0 space-y-6">
                    <Card className="glass-panel border-primary/20">
                        <CardHeader>
                            <CardTitle className="text-xs uppercase tracking-widest flex items-center">
                                <Zap className="w-4 h-4 mr-2 text-primary" />
                                AUTO-STATS
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 font-mono">
                            <div className="flex justify-between items-center text-xs">
                                <span className="text-muted-foreground">AUTO-EXECUTION RATE</span>
                                <span className="text-primary font-bold">92.4%</span>
                            </div>
                            <div className="flex justify-between items-center text-xs">
                                <span className="text-muted-foreground">TIME SAVED / 24H</span>
                                <span className="text-primary font-bold">148 HRS</span>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="flex-1 glass-panel border-border/50 overflow-hidden flex flex-col">
                        <CardHeader className="bg-muted/30 border-b border-border">
                            <CardTitle className="text-xs uppercase tracking-widest flex items-center">
                                <History className="w-4 h-4 mr-2 text-muted-foreground" />
                                RECENT RUNS
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 p-0 overflow-y-auto custom-scrollbar">
                            {[1, 2, 3, 4, 5].map(i => (
                                <div key={i} className="p-4 border-b border-border/50 hover:bg-muted/20 transition-colors flex items-center justify-between group cursor-pointer">
                                    <div className="flex items-center space-x-3">
                                        <div className="p-2 rounded bg-muted/50">
                                            <CheckCircle2 size={14} className="text-primary" />
                                        </div>
                                        <div>
                                            <p className="text-xs font-bold">Threat Isolation #{1000 + i}</p>
                                            <p className="text-[10px] text-muted-foreground">Completed • Today, 10:4{i} AM</p>
                                        </div>
                                    </div>
                                    <ArrowRight size={14} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-1" />
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default SOARPage;
