import React, { useState, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    GitGraph,
    ZoomIn,
    ZoomOut,
    ShieldAlert,
    Share2,
    Zap,
    Target,
    Terminal,
    CheckCircle2,
    ShieldCheck,
    HelpCircle,
    Activity,
    Lock,
    Link as LinkIcon
} from 'lucide-react';

const MotionCircle = motion.circle;
const MotionDiv = motion.div;
const MotionG = motion.g;
const MotionLine = motion.line;

const AttackGraphPage = () => {
    const [selectedNode, setSelectedNode] = useState(null);
    const [isolationResult, setIsolationResult] = useState('');
    const [segmentationViolations, setSegmentationViolations] = useState([
        { id: 'vio-01', source: 'DMZ-Web-Server', dest: 'SQL-DB-Cluster', rule: 'VLAN Segmentation: Direct access prohibited', status: 'critical' },
        { id: 'vio-02', source: 'DevOps-Workstation', dest: 'Domain-Controller', rule: 'Identity Enforcement: Non-authenticated AD RPC call', status: 'high' }
    ]);

    // Attack Path Node Network
    const nodes = useMemo(() => [
        { id: 'n1', x: 120, y: 200, label: "Perimeter Router", type: "gateway", status: "compromised", ip: '185.220.101.5', risk: 100, details: 'Initial breach target. Actively routing malicious Tor exfiltrations.' },
        { id: 'n2', x: 300, y: 120, label: "DMZ Web Server", type: "server", status: "compromised", ip: '10.0.0.5', risk: 85, details: 'Infected with reverse shell payload following HTTP exploit. Actively scanning internal VLANs.' },
        { id: 'n3', x: 300, y: 280, label: "DevOps Workstation", type: "workstation", status: "suspicious", ip: '192.168.2.141', risk: 64, details: 'Demonstrating credential misuse triggers. Running compiled payloads.' },
        { id: 'n4', x: 500, y: 120, label: "SQL Database", type: "database", status: "target", ip: '10.0.0.12', risk: 90, details: 'Target of SQL staging dump files. Holds critical CHD records.' },
        { id: 'n5', x: 500, y: 280, label: "Billing App Server", type: "server", status: "safe", ip: '10.0.0.8', risk: 12, details: 'Standard application instance. Segmentation rules active.' },
        { id: 'n6', x: 680, y: 200, label: "Active Directory DC", type: "crown_jewel", status: "threatened", ip: '192.168.1.10', risk: 95, details: 'Ultimate attack objective. Lateral remote PowerShell attempts identified from compromised hosts.' }
    ], []);

    const links = useMemo(() => [
        { from: 'n1', to: 'n2', risk: 'Critical', vector: 'RCE HTTP Exploit' },
        { from: 'n1', to: 'n3', risk: 'High', vector: 'Phished Credentials' },
        { from: 'n2', to: 'n4', risk: 'Critical', vector: 'VLAN Segmentation Bypass' },
        { from: 'n2', to: 'n5', risk: 'Medium', vector: 'Subnet Scanning' },
        { from: 'n4', to: 'n6', risk: 'Critical', vector: 'AD Privilege Escalation' },
        { from: 'n3', to: 'n6', risk: 'High', vector: 'Kerberos Pass-the-Ticket' }
    ], []);

    const activeNode = selectedNode || nodes.find(x => x.status === 'crown_jewel');

    const handleNodeClick = (node) => {
        setSelectedNode(node);
        setIsolationResult('');
    };

    const triggerNodeIsolation = (nodeId) => {
        const n = nodes.find(x => x.id === nodeId);
        setIsolationResult(`[+] Deploying agent countermeasure to host: ${n?.label} [${n?.ip}]...\n[+] Closing TCP sockets...\n[+] Applying localized IPTABLES block...\n[+] Containment complete. Node ISOLATED.`);

        // Remove isolation violation alerts related to this host
        setSegmentationViolations(prev => prev.filter(x => x.source !== n?.label));
    };

    const getStatusColor = (status) => {
        const lower = status.toLowerCase();
        if (lower === 'compromised') return 'stroke-red-500 fill-red-950/20';
        if (lower === 'suspicious') return 'stroke-amber-500 fill-amber-950/20';
        if (lower === 'threatened') return 'stroke-purple-500 fill-purple-950/20';
        if (lower === 'crown_jewel') return 'stroke-yellow-500 fill-yellow-950/20';
        return 'stroke-emerald-500 fill-emerald-950/20';
    };

    return (
        <div className="h-full flex flex-col space-y-6">
            <PageHeader
                title="NEO4J LATERAL MOVEMENT MAPPING"
                subtitle="Visual correlation of multi-stage attack paths, lateral jumps, and asset blast radius."
                actions={
                    <div className="flex items-center space-x-2">
                        <Badge className="bg-red-500/20 text-red-400 border border-red-500/30 font-mono text-[9px] px-3.5 py-1.5 animate-pulse">
                            CRITICAL PATH DETECTED
                        </Badge>
                    </div>
                }
            />

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
                {/* SVG Graph Canvas */}
                <Card className="lg:col-span-8 glass-panel border-primary/20 overflow-hidden relative flex flex-col min-h-[480px]">
                    <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />

                    <CardHeader className="pb-3 border-b border-white/5 bg-muted/10 flex flex-row justify-between items-center z-10">
                        <div>
                            <CardTitle className="text-xs uppercase tracking-widest text-white flex items-center">
                                <GitGraph className="w-4 h-4 mr-2 text-primary" />
                                THREAT PROPAGATION TOPOLOGY
                            </CardTitle>
                        </div>
                        <div className="flex space-x-1.5">
                            <Button variant="outline" size="sm" className="h-7 w-7 p-0 border-white/5 text-white">
                                <ZoomIn className="w-3.5 h-3.5" />
                            </Button>
                            <Button variant="outline" size="sm" className="h-7 w-7 p-0 border-white/5 text-white">
                                <ZoomOut className="w-3.5 h-3.5" />
                            </Button>
                        </div>
                    </CardHeader>

                    <CardContent className="flex-1 p-0 relative flex items-center justify-center bg-black/40">
                        <svg viewBox="0 0 800 400" className="w-full h-auto max-h-[380px] p-6">
                            <defs>
                                <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6" className="opacity-70" />
                                </marker>
                                <marker id="arrow-red" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
                                </marker>
                            </defs>

                            {/* Draw Link Paths */}
                            {links.map((link, idx) => {
                                const fromNode = nodes.find(n => n.id === link.from);
                                const toNode = nodes.find(n => n.id === link.to);
                                if (!fromNode || !toNode) return null;
                                const isCritical = link.risk === 'Critical';

                                return (
                                    <g key={`link-${idx}`}>
                                        {/* Background glow path */}
                                        <line
                                            x1={fromNode.x} y1={fromNode.y}
                                            x2={toNode.x} y2={toNode.y}
                                            stroke={isCritical ? '#ef4444' : '#8b5cf6'}
                                            strokeWidth={isCritical ? '4' : '2'}
                                            className="opacity-15 blur-sm"
                                        />

                                        {/* Core path line */}
                                        <MotionLine
                                            x1={fromNode.x} y1={fromNode.y}
                                            x2={toNode.x} y2={toNode.y}
                                            stroke={isCritical ? '#ef4444' : '#8b5cf6'}
                                            strokeWidth="1.5"
                                            strokeDasharray="4 4"
                                            markerEnd={isCritical ? "url(#arrow-red)" : "url(#arrow)"}
                                            initial={{ pathLength: 0 }}
                                            animate={{ pathLength: 1 }}
                                            transition={{ duration: 1.2, delay: idx * 0.2 }}
                                        />

                                        {/* Animated Alert Pulse */}
                                        <MotionCircle
                                            r="4.5"
                                            fill={isCritical ? '#ef4444' : '#8b5cf6'}
                                            className="shadow-lg"
                                            animate={{
                                                cx: [fromNode.x, toNode.x],
                                                cy: [fromNode.y, toNode.y]
                                            }}
                                            transition={{ duration: 2.2, repeat: Infinity, ease: 'linear', delay: idx * 0.3 }}
                                        />
                                    </g>
                                );
                            })}

                            {/* Draw Nodes */}
                            {nodes.map((node, i) => {
                                const isActive = activeNode.id === node.id;
                                const isCompromised = node.status === 'compromised';
                                const isTarget = node.status === 'crown_jewel';

                                return (
                                    <MotionG
                                        key={node.id}
                                        onClick={() => handleNodeClick(node)}
                                        className="cursor-pointer group"
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        transition={{ type: 'spring', delay: i * 0.15 }}
                                    >
                                        {/* Pulse Halo for Active/Threatened Nodes */}
                                        {(isActive || isCompromised || node.status === 'threatened') && (
                                            <MotionCircle
                                                cx={node.x} cy={node.y} r="28"
                                                fill="none"
                                                stroke={isCompromised ? '#ef4444' : isTarget ? '#eab308' : '#8b5cf6'}
                                                strokeWidth="1"
                                                animate={{ scale: [1, 1.25], opacity: [0.6, 0] }}
                                                transition={{ duration: 1.8, repeat: Infinity }}
                                            />
                                        )}

                                        {/* Core Circle */}
                                        <circle
                                            cx={node.x} cy={node.y} r="20"
                                            className={`stroke-[2.5] fill-[#0d121f] transition-all group-hover:stroke-[3.5] ${getStatusColor(node.status)}`}
                                        />

                                        {/* Icons in Circle */}
                                        <g className="pointer-events-none">
                                            {isTarget ? (
                                                <Target x={node.x - 8} y={node.y - 8} size={16} className="text-yellow-500" />
                                            ) : isCompromised ? (
                                                <ShieldAlert x={node.x - 8} y={node.y - 8} size={16} className="text-red-500 animate-pulse" />
                                            ) : (
                                                <Zap x={node.x - 8} y={node.y - 8} size={16} className="text-primary" />
                                            )}
                                        </g>

                                        {/* Node Label Text */}
                                        <text
                                            x={node.x} y={node.y + 36}
                                            textAnchor="middle"
                                            className={`text-[9px] font-black tracking-tighter uppercase font-mono ${
                                                isActive ? 'fill-primary' : 'fill-white'
                                            }`}
                                        >
                                            {node.label}
                                        </text>

                                        <text
                                            x={node.x} y={node.y + 45}
                                            textAnchor="middle"
                                            className="fill-muted-foreground text-[8px] font-mono"
                                        >
                                            {node.ip}
                                        </text>
                                    </MotionG>
                                );
                            })}
                        </svg>
                    </CardContent>
                </Card>

                {/* Right Column: Node Details & Segmentation Alerts */}
                <div className="lg:col-span-4 space-y-6 flex flex-col min-h-0">
                    {/* BLAST RADIUS CARD */}
                    <Card className="glass-panel border-red-500/20">
                        <CardHeader className="pb-3 border-b border-white/5 bg-red-950/5">
                            <CardTitle className="text-xs uppercase tracking-widest text-red-400 flex items-center">
                                <ShieldAlert className="w-4 h-4 mr-2 animate-pulse" />
                                THREAT BLAST RADIUS IMPACT
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 space-y-3.5">
                            <div className="flex justify-between items-end">
                                <span className="text-[10px] font-mono text-muted-foreground uppercase">Threat Host Penetration</span>
                                <span className="text-2xl font-black font-mono text-red-500">82% RISK</span>
                            </div>
                            <div className="w-full bg-[#182030] h-1.5 rounded-full overflow-hidden">
                                <MotionDiv
                                    className="h-full bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.8)]"
                                    initial={{ width: 0 }}
                                    animate={{ width: '82%' }}
                                    transition={{ duration: 1.2 }}
                                />
                            </div>
                            <p className="text-[10px] text-muted-foreground font-mono leading-relaxed">
                                Compromise of DMZ Web Server and DevOps Workspace offers a lateral escalation pathway directly to the Domain Controller. Domain breach expected within <span className="text-white font-bold">14 minutes</span> without containment.
                            </p>
                        </CardContent>
                    </Card>

                    {/* CLICKED NODE DETAIL SIDEBAR */}
                    <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                        <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                            <div className="flex items-center space-x-2">
                                <Activity className="w-4 h-4 text-primary animate-pulse" />
                                <CardTitle className="text-xs uppercase tracking-widest text-white">NODE METRICS ANALYSIS</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-4">
                            <div className="space-y-1">
                                <h4 className="text-xs font-black text-white uppercase">{activeNode.label}</h4>
                                <p className="text-[9px] font-mono text-muted-foreground">NODE IP: {activeNode.ip} • TYPE: {activeNode.type}</p>
                            </div>

                            <div className="p-3 rounded-lg bg-black border border-white/5 space-y-2 text-xs font-mono">
                                <div className="flex justify-between items-center text-[10px] uppercase font-bold text-muted-foreground border-b border-white/5 pb-1">
                                    <span>POSTURE METRIC</span>
                                    <span>VALUE</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-muted-foreground">Exploit Exposure</span>
                                    <span className="text-red-400 font-bold">{activeNode.risk}%</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-muted-foreground">Audit Status</span>
                                    <span className="text-white uppercase font-bold">{activeNode.status}</span>
                                </div>
                                <p className="text-[10px] text-muted-foreground leading-relaxed pt-2 border-t border-white/5">
                                    <span className="text-primary font-bold">Details:</span> {activeNode.details}
                                </p>
                            </div>

                            {/* Containment action triggers */}
                            <div className="space-y-2">
                                <Button
                                    onClick={() => triggerNodeIsolation(activeNode.id)}
                                    className="w-full bg-red-950 hover:bg-red-900 border border-red-500/20 text-red-300 text-[10px] font-bold h-9 flex items-center justify-center space-x-1.5 transition-colors"
                                >
                                    <Lock className="w-3.5 h-3.5" />
                                    <span>CONTAIN NODE ({activeNode.label})</span>
                                </Button>
                            </div>

                            {/* Isolation Console output */}
                            {isolationResult && (
                                <div className="p-3 rounded-lg bg-black border border-white/5 flex flex-col">
                                    <div className="flex justify-between items-center mb-1 text-[8px] font-mono text-muted-foreground uppercase">
                                        <span>Containment logs</span>
                                        <span className="text-emerald-400 font-bold">completed</span>
                                    </div>
                                    <pre className="text-[9px] font-mono leading-relaxed text-glow-primary text-primary overflow-x-auto whitespace-pre-wrap">
                                        {isolationResult}
                                    </pre>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* SEGMENTATION VIOLATIONS */}
                    <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                        <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                            <CardTitle className="text-xs uppercase tracking-widest text-white flex items-center">
                                <LinkIcon className="w-4 h-4 mr-2 text-primary" />
                                SEGMENTATION VIOLATIONS
                                <Badge className="ml-2 bg-primary/20 text-primary border-primary/30 text-[8px] font-mono">
                                    {segmentationViolations.length}
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 flex-1 overflow-y-auto custom-scrollbar">
                            <div className="divide-y divide-white/5">
                                {segmentationViolations.length === 0 ? (
                                    <div className="p-4 text-center text-xs text-muted-foreground italic">
                                        <ShieldCheck className="w-6 h-6 text-emerald-400 mx-auto mb-1" />
                                        Subnet boundaries aligned with Zero-Trust guidelines.
                                    </div>
                                ) : (
                                    segmentationViolations.map((vio) => (
                                        <div key={vio.id} className="p-3 hover:bg-muted/10 transition-colors space-y-1">
                                            <div className="flex justify-between items-center">
                                                <Badge className="bg-red-500/10 text-red-400 border border-red-500/20 text-[8px] font-mono">
                                                    {vio.status.toUpperCase()}
                                                </Badge>
                                                <span className="text-[9px] font-mono text-muted-foreground">ID: {vio.id}</span>
                                            </div>
                                            <p className="text-[11px] text-white font-mono font-bold leading-tight">
                                                {vio.source} ➔ {vio.dest}
                                            </p>
                                            <p className="text-[9px] text-muted-foreground font-mono leading-relaxed">{vio.rule}</p>
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default AttackGraphPage;
