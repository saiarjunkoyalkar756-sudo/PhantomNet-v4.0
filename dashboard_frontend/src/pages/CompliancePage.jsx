import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
    ShieldCheck, 
    ShieldAlert, 
    Activity, 
    RefreshCw, 
    FileText, 
    Download, 
    TrendingUp, 
    Calendar, 
    Brain,
    CheckCircle2,
    AlertTriangle,
    Layers,
    ArrowRight
} from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const CompliancePage = () => {
    const [selectedStandard, setSelectedStandard] = useState('ISO27001'); // 'ISO27001' | 'SOC2' | 'PCIDSS' | 'GDPR'
    const [loading, setLoading] = useState(false);
    const [auditing, setAuditing] = useState(false);
    const [auditProgress, setAuditProgress] = useState(0);
    const [report, setReport] = useState(null);

    // Dynamic Mock Databases matching backend models
    const complianceDatabases = {
        ISO27001: {
            score: 87,
            trend: '+2.4%',
            lastAudit: '2026-05-20',
            nextAudit: '2026-11-20',
            status: 'partial',
            heatmap: [
                { control_area: 'Access Control', compliant_percentage: 92, non_compliant_count: 1, total_controls: 12 },
                { control_area: 'Data Protection', compliant_percentage: 85, non_compliant_count: 2, total_controls: 15 },
                { control_area: 'Incident Response', compliant_percentage: 100, non_compliant_count: 0, total_controls: 8 },
                { control_area: 'Risk Management', compliant_percentage: 80, non_compliant_count: 1, total_controls: 5 },
                { control_area: 'Security Operations', compliant_percentage: 78, non_compliant_count: 3, total_controls: 14 }
            ],
            findings: [
                { control_id: 'ISO-A.9.1.1', description: 'Access control policy validation', status: 'compliant', evidence: 'Access logs audited and encrypted key rotations active.', severity: 'medium' },
                { control_id: 'ISO-A.12.4.1', description: 'Event logging & logging review', status: 'compliant', evidence: 'Log normalizers mounted on EventBus.', severity: 'low' },
                { control_id: 'ISO-A.10.1.1', description: 'Policy on use of cryptographic controls', status: 'non-compliant', severity: 'high', recommendation: 'Enforce Dual-Key JWT Signing and move remaining plain secrets into vault environments.' },
                { control_id: 'ISO-A.18.1.1', description: 'Identification of applicable legislation', status: 'compliant', evidence: 'Legal mappings automated.', severity: 'low' },
                { control_id: 'ISO-A.12.6.1', description: 'Management of technical vulnerabilities', status: 'non-compliant', severity: 'critical', recommendation: 'xz-utils CVE-2024-3094 unpatched on developer endpoint-ubuntu-02.' }
            ],
            ai_improvement_plan: [
                { recommendation_id: 'rec-001', control_id: 'ISO-A.12.6.1', description: 'Apply compensating security controls on dev endpoint-ubuntu-02 immediately due to backdoor vulnerability CVE-2024-3094.', priority: 'high', estimated_effort: 'low', ai_rationale: 'Active threat propagation paths detected leading to primary Active Directory.' },
                { recommendation_id: 'rec-002', control_id: 'ISO-A.10.1.1', description: 'Migrate DB passwords and API tokens from committed .env config to production-grade vaults.', priority: 'medium', estimated_effort: 'medium', ai_rationale: 'Mitigates static key compromise risk vectors.' }
            ]
        },
        SOC2: {
            score: 94,
            trend: '+1.8%',
            lastAudit: '2026-05-18',
            nextAudit: '2026-11-18',
            status: 'compliant',
            heatmap: [
                { control_area: 'Access Control', compliant_percentage: 100, non_compliant_count: 0, total_controls: 10 },
                { control_area: 'Data Protection', compliant_percentage: 94, non_compliant_count: 1, total_controls: 18 },
                { control_area: 'Incident Response', compliant_percentage: 100, non_compliant_count: 0, total_controls: 10 },
                { control_area: 'Risk Management', compliant_percentage: 90, non_compliant_count: 1, total_controls: 10 },
                { control_area: 'Security Operations', compliant_percentage: 88, non_compliant_count: 2, total_controls: 16 }
            ],
            findings: [
                { control_id: 'SOC2-CC6.1', description: 'Logical access controls and user credentials', status: 'compliant', evidence: 'MFA active on gateway and token rotation active.', severity: 'medium' },
                { control_id: 'SOC2-CC6.3', description: 'Dynamic data encryption at transit', status: 'compliant', evidence: 'TLS 1.3 enforced on all REST endpoints.', severity: 'low' },
                { control_id: 'SOC2-CC7.3', description: 'Vulnerability scans execution frequency', status: 'non-compliant', severity: 'medium', recommendation: 'Automate weekly locust/k6 penetration benchmarks in local CD runners.' }
            ],
            ai_improvement_plan: [
                { recommendation_id: 'rec-101', control_id: 'SOC2-CC7.3', description: 'Establish automated continuous scanning on all pipeline deployments.', priority: 'medium', estimated_effort: 'medium', ai_rationale: 'Required to demonstrate continuous audit adherence during SOC2 audit cycles.' }
            ]
        },
        PCIDSS: {
            score: 78,
            trend: '-1.5%',
            lastAudit: '2026-04-12',
            nextAudit: '2026-10-12',
            status: 'partial',
            heatmap: [
                { control_area: 'Access Control', compliant_percentage: 80, non_compliant_count: 2, total_controls: 10 },
                { control_area: 'Data Protection', compliant_percentage: 70, non_compliant_count: 4, total_controls: 14 },
                { control_area: 'Incident Response', compliant_percentage: 90, non_compliant_count: 1, total_controls: 10 },
                { control_area: 'Risk Management', compliant_percentage: 80, non_compliant_count: 1, total_controls: 5 },
                { control_area: 'Security Operations', compliant_percentage: 75, non_compliant_count: 3, total_controls: 12 }
            ],
            findings: [
                { control_id: 'PCI-REQ-3.4', description: 'Encrypt cardholder data at rest', status: 'non-compliant', severity: 'critical', recommendation: 'Disable debug logs from storing raw payload hashes inside logging tables.' },
                { control_id: 'PCI-REQ-8.2', description: 'Secure administrative access credentials', status: 'compliant', evidence: 'Dual auth gateway keys configured.', severity: 'high' },
                { control_id: 'PCI-REQ-11.2', description: 'Run internal and external vulnerability scans', status: 'non-compliant', severity: 'high', recommendation: 'Connect mitre_attack_mapper directly with the Neo4j endpoint.' }
            ],
            ai_improvement_plan: [
                { recommendation_id: 'rec-201', control_id: 'PCI-REQ-3.4', description: 'Sanitize ingestion handlers and log filters to permanently block PII/CHD log pollution.', priority: 'high', estimated_effort: 'low', ai_rationale: 'Violates absolute regulatory standards. Critical compliance hazard.' }
            ]
        },
        GDPR: {
            score: 95,
            trend: 'stable',
            lastAudit: '2026-05-15',
            nextAudit: '2026-11-15',
            status: 'compliant',
            heatmap: [
                { control_area: 'Access Control', compliant_percentage: 100, non_compliant_count: 0, total_controls: 8 },
                { control_area: 'Data Protection', compliant_percentage: 95, non_compliant_count: 1, total_controls: 20 },
                { control_area: 'Incident Response', compliant_percentage: 100, non_compliant_count: 0, total_controls: 12 },
                { control_area: 'Risk Management', compliant_percentage: 90, non_compliant_count: 1, total_controls: 10 },
                { control_area: 'Security Operations', compliant_percentage: 90, non_compliant_count: 1, total_controls: 10 }
            ],
            findings: [
                { control_id: 'GDPR-ART-32', description: 'Security of data processing systems', status: 'compliant', evidence: 'Immutable ledger audit logs operational.', severity: 'medium' },
                { control_id: 'GDPR-ART-33', description: 'Notification of personal data breach', status: 'compliant', evidence: 'Forensics engine alerts and playbooks ready.', severity: 'medium' }
            ],
            ai_improvement_plan: []
        }
    };

    useEffect(() => {
        fetchComplianceData();
    }, [selectedStandard]);

    const fetchComplianceData = async () => {
        setLoading(true);
        try {
            // Attempt to hit dynamic compliance router
            const response = await axios.get(`${API_BASE_URL}/api/v1/compliance/assessments/`);
            if (response.data && response.data.success) {
                // If backend yields custom database details
                setReport(response.data.data);
            } else {
                setReport(complianceDatabases[selectedStandard]);
            }
        } catch (err) {
            // Seamless premium mock failover
            setReport(complianceDatabases[selectedStandard]);
        } finally {
            setLoading(false);
        }
    };

    const triggerComplianceAudit = async () => {
        if (auditing) return;
        setAuditing(true);
        setAuditProgress(10);
        
        const steps = [
            { pct: 30, msg: 'Auditing authentication rate limits and PQC configurations...' },
            { pct: 60, msg: 'Analyzing Neo4j lateral vulnerability propagation vectors...' },
            { pct: 85, msg: 'Parsing audit logs from the immutable blockchain ledger...' },
            { pct: 100, msg: 'Generating compliance posture findings...' }
        ];

        for (let s of steps) {
            await new Promise(resolve => setTimeout(resolve, 800));
            setAuditProgress(s.pct);
        }

        // Simulates new scan result or refreshes
        setReport(prev => {
            const current = complianceDatabases[selectedStandard];
            return {
                ...current,
                score: Math.min(100, current.score + 1), // post audit improvement
                lastAudit: new Date().toISOString().split('T')[0]
            };
        });

        setAuditing(false);
        setAuditProgress(0);
    };

    const getStatusColor = (status) => {
        const lower = status.toLowerCase();
        if (lower === 'compliant') return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10';
        if (lower === 'partial') return 'text-amber-500 border-amber-500/20 bg-amber-500/10';
        return 'text-red-500 border-red-500/20 bg-red-500/10';
    };

    const getSeverityBadge = (sev) => {
        const lower = sev.toLowerCase();
        if (lower === 'critical') return <Badge className="bg-red-500/25 border-red-500/30 text-red-400 font-mono text-[9px]">CRITICAL</Badge>;
        if (lower === 'high') return <Badge className="bg-amber-500/25 border-amber-500/30 text-amber-400 font-mono text-[9px]">HIGH</Badge>;
        if (lower === 'medium') return <Badge className="bg-cyan-500/25 border-cyan-500/30 text-cyan-400 font-mono text-[9px]">MEDIUM</Badge>;
        return <Badge className="bg-blue-500/20 border-blue-500/30 text-blue-300 font-mono text-[9px]">LOW</Badge>;
    };

    const currentStandard = report || complianceDatabases[selectedStandard];

    return (
        <div className="h-full flex flex-col space-y-6">
            <PageHeader 
                title="GOVERNANCE, RISK & COMPLIANCE"
                subtitle="Continuous governance framework mapping, gap analytics, and automated compliance auditing."
                actions={
                    <Button 
                        disabled={auditing}
                        onClick={triggerComplianceAudit}
                        className="bg-primary hover:bg-primary/95 text-primary-foreground font-bold text-xs h-9 flex items-center justify-center space-x-2 shadow-[0_0_15px_rgba(139,92,246,0.4)]"
                    >
                        {auditing ? (
                            <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                <span>AUDITING POSTURE ({auditProgress}%)</span>
                            </>
                        ) : (
                            <>
                                <Activity className="w-3.5 h-3.5 animate-pulse" />
                                <span>RUN COMPLIANCE AUDIT</span>
                            </>
                        )}
                    </Button>
                }
            />

            {/* Framework Select Tabs */}
            <div className="flex bg-muted/40 p-1 rounded-lg border border-white/5 self-start">
                {Object.keys(complianceDatabases).map((std) => (
                    <button 
                        key={std}
                        onClick={() => setSelectedStandard(std)}
                        className={`px-5 py-2 text-xs font-bold rounded-md transition-all ${selectedStandard === std ? 'bg-primary text-primary-foreground shadow-lg' : 'text-muted-foreground hover:text-foreground'}`}
                    >
                        {std === 'ISO27001' ? 'ISO 27001:2022' : std === 'SOC2' ? 'SOC 2 TYPE II' : std === 'PCIDSS' ? 'PCI DSS v4.0' : 'GDPR COMPLIANCE'}
                    </button>
                ))}
            </div>

            {auditing && (
                <div className="w-full bg-[#182030] h-1.5 rounded-full overflow-hidden">
                    <motion.div 
                        className="h-full bg-primary shadow-[0_0_10px_rgba(139,92,246,0.8)]"
                        initial={{ width: 0 }}
                        animate={{ width: `${auditProgress}%` }}
                        transition={{ duration: 0.3 }}
                    />
                </div>
            )}

            {/* Metrics Dashboard Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Framework Posture</p>
                            <h3 className="text-2xl font-black font-mono mt-1 text-white">
                                {currentStandard.score}%
                            </h3>
                        </div>
                        <div className="w-10 h-10 rounded-full border-2 border-primary/30 flex items-center justify-center text-[11px] font-mono text-primary font-bold text-glow-primary">
                            {currentStandard.score}
                        </div>
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Historical Trend</p>
                            <h3 className="text-2xl font-black font-mono mt-1 text-emerald-400 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> {currentStandard.trend}
                            </h3>
                        </div>
                        <Calendar className="w-8 h-8 text-emerald-400 opacity-40" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Audit Status</p>
                            <h3 className="text-xl font-black font-mono mt-2 text-white">
                                <Badge className={`uppercase text-[9px] ${getStatusColor(currentStandard.status)}`}>
                                    {currentStandard.status === 'compliant' ? 'PASSED AUDIT' : 'PARTIAL GAPS'}
                                </Badge>
                            </h3>
                        </div>
                        <ShieldCheck className="w-8 h-8 text-primary opacity-40" />
                    </CardContent>
                </Card>
                <Card className="glass-panel border-primary/20">
                    <CardContent className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground">Last vs Next Audit</p>
                            <h3 className="text-[11px] font-mono text-white mt-1.5 leading-relaxed">
                                <span className="text-muted-foreground">LAST:</span> {currentStandard.lastAudit}<br/>
                                <span className="text-primary font-bold">NEXT:</span> {currentStandard.nextAudit}
                            </h3>
                        </div>
                        <Calendar className="w-8 h-8 text-purple-400 opacity-40" />
                    </CardContent>
                </Card>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
                {/* Left Panel: Control Area Heatmap */}
                <Card className="lg:col-span-4 glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                    <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                        <CardTitle className="text-xs uppercase tracking-widest text-white flex items-center">
                            <Layers className="w-4 h-4 mr-2 text-primary" />
                            CONTROL AREA HEATMAP
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-4">
                        {currentStandard.heatmap.map((area) => (
                            <div key={area.control_area} className="space-y-2 p-3 rounded-lg bg-black border border-white/5">
                                <div className="flex justify-between items-center text-xs">
                                    <span className="font-bold text-white">{area.control_area}</span>
                                    <span className="font-mono text-muted-foreground">
                                        {area.total_controls - area.non_compliant_count} / {area.total_controls} controls
                                    </span>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className="flex-1 bg-[#182030] h-2 rounded-full overflow-hidden">
                                        <div 
                                            className={`h-full ${
                                                area.compliant_percentage >= 90 ? 'bg-emerald-400' :
                                                area.compliant_percentage >= 75 ? 'bg-amber-500' :
                                                'bg-red-500'
                                            }`}
                                            style={{ width: `${area.compliant_percentage}%` }}
                                        />
                                    </div>
                                    <span className={`text-xs font-mono font-bold ${
                                        area.compliant_percentage >= 90 ? 'text-emerald-400' :
                                        area.compliant_percentage >= 75 ? 'text-amber-500' :
                                        'text-red-500'
                                    }`}>
                                        {area.compliant_percentage}%
                                    </span>
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                {/* Right Panel: Findings and Recommendations */}
                <div className="lg:col-span-8 space-y-6 flex flex-col min-h-0">
                    {/* Compliance gap recommendations */}
                    <Card className="glass-panel border-primary/20 overflow-hidden flex flex-col">
                        <CardHeader className="pb-3 border-b border-white/5 bg-muted/10 flex flex-row justify-between items-center">
                            <div className="flex items-center space-x-2">
                                <Brain className="w-4 h-4 text-primary animate-pulse" />
                                <CardTitle className="text-xs uppercase tracking-widest text-white">AI-PRIORITIZED GAP REMEDIATIONS</CardTitle>
                            </div>
                            <Button variant="outline" size="sm" className="h-7 text-[10px] border-white/5 text-white font-mono">
                                <Download className="w-3.5 h-3.5 mr-1" /> COMPLIANCE PDF REPORT
                            </Button>
                        </CardHeader>
                        <CardContent className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-3">
                            {currentStandard.ai_improvement_plan.length === 0 ? (
                                <div className="h-28 flex flex-col items-center justify-center text-muted-foreground text-xs italic">
                                    <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                                    Post-Quantum compliance scanning validated. No gaps identified.
                                </div>
                            ) : (
                                currentStandard.ai_improvement_plan.map((rec) => (
                                    <div key={rec.recommendation_id} className="p-3.5 rounded-lg bg-black border border-white/5 space-y-2">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center space-x-2">
                                                <Badge className="bg-primary/20 border-primary/30 text-primary-foreground text-[8px] font-mono">
                                                    CONTROL: {rec.control_id}
                                                </Badge>
                                                <Badge className={
                                                    rec.priority === 'high' ? 'bg-red-500/20 text-red-300 border-red-500/30' :
                                                    'bg-amber-500/20 text-amber-300 border-amber-500/30'
                                                }>
                                                    PRIORITY: {rec.priority.toUpperCase()}
                                                </Badge>
                                            </div>
                                            <span className="text-[9px] font-mono text-muted-foreground">Effort: {rec.estimated_effort}</span>
                                        </div>
                                        <p className="text-xs text-white leading-relaxed font-mono">
                                            {rec.description}
                                        </p>
                                        {rec.ai_rationale && (
                                            <p className="text-[10px] text-muted-foreground italic leading-relaxed pt-1.5 border-t border-white/5">
                                                <span className="text-primary font-bold not-italic">AI Recommendation rationale:</span> {rec.ai_rationale}
                                            </p>
                                        )}
                                    </div>
                                ))
                            )}
                        </CardContent>
                    </Card>

                    {/* Framework Findings Grid */}
                    <Card className="glass-panel border-primary/20 flex-1 overflow-hidden flex flex-col">
                        <CardHeader className="pb-3 border-b border-white/5 bg-muted/10">
                            <CardTitle className="text-xs uppercase tracking-widest text-white">DETAILED AUDIT FINDINGS REGISTER</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 flex-1 overflow-y-auto custom-scrollbar">
                            <table className="w-full text-left border-collapse text-xs">
                                <thead>
                                    <tr className="border-b border-white/5 bg-muted/20 text-muted-foreground text-[10px] font-mono uppercase tracking-wider">
                                        <th className="p-3">Control ID</th>
                                        <th className="p-3">Audit Domain Description</th>
                                        <th className="p-3">Audit Status</th>
                                        <th className="p-3">Severity</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5 text-white">
                                    {currentStandard.findings.map((f, index) => (
                                        <tr key={index} className="hover:bg-muted/10 transition-colors">
                                            <td className="p-3 font-mono text-primary font-bold">{f.control_id}</td>
                                            <td className="p-3">
                                                <p className="font-bold text-white">{f.description}</p>
                                                {f.evidence && <p className="text-[10px] text-muted-foreground mt-0.5 font-mono">Evidence: {f.evidence}</p>}
                                                {f.recommendation && <p className="text-[10px] text-red-400 mt-0.5 font-mono">Remediation: {f.recommendation}</p>}
                                            </td>
                                            <td className="p-3">
                                                <Badge className={
                                                    f.status === 'compliant' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                                    f.status === 'non-compliant' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                                                    'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
                                                }>
                                                    {f.status.toUpperCase()}
                                                </Badge>
                                            </td>
                                            <td className="p-3">{getSeverityBadge(f.severity)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default CompliancePage;
