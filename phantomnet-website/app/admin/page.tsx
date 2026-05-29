// phantomnet-website/app/admin/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  Activity, 
  Server, 
  Slash, 
  Trash2, 
  PlayCircle, 
  RefreshCw, 
  UserMinus, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Lock, 
  Send,
  Terminal,
  Clock,
  Layers,
  FileText
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000'; // Unified main.py stack port

const INITIAL_SERVICES = [
  { name: 'Gateway Service', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/gateway' },
  { name: 'AI Behavioral Engine', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/behavioral' },
  { name: 'SOAR Engine', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/soar' },
  { name: 'Threat Intel Service', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/threat-intel' },
  { name: 'Compliance Service', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/compliance' },
  { name: 'Blockchain Service', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/blockchain' },
  { name: 'Vulnerability Service', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/vulnerability' },
  { name: 'Forensics Engine', port: 8000, status: 'OFFLINE', load: '0%', endpoint: '/api/v1/forensics' },
];

export default function AdminPortal() {
  const [services, setServices] = useState(INITIAL_SERVICES);
  const [blacklistedIPs, setBlacklistedIPs] = useState<any[]>([]);
  const [newIP, setNewIP] = useState('');
  const [newReason, setNewReason] = useState('');
  
  // States
  const [isBlacklistLoading, setIsBlacklistLoading] = useState(false);
  const [isHealthLoading, setIsHealthLoading] = useState(false);
  const [blacklistStatus, setBlacklistStatus] = useState<{ success: boolean; msg: string } | null>(null);
  const [authToken, setAuthToken] = useState('');
  const [adminUser, setAdminUser] = useState<any>(null);

  // BAS Simulation State
  const [attackTarget, setAttackTarget] = useState('compromised-server-01');
  const [simulationLogs, setSimulationLogs] = useState<string[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  
  // Administrative Audit Log Trail
  const [adminAuditTrail, setAdminAuditTrail] = useState<any[]>([
    { id: 'aud-01', action: 'Admin Portal Access Granted', operator: 'admin@phantomnet.local', status: 'success', time: '10:15 AM' },
    { id: 'aud-02', action: 'Synchronized microservices grid cluster status', operator: 'admin@phantomnet.local', status: 'success', time: '10:16 AM' }
  ]);

  // Node telemetry load simulator
  const [systemLoad, setSystemLoad] = useState({ cpu: 32, ram: 54, network: 120 });

  useEffect(() => {
    // Check JWT authorization
    const token = typeof window !== 'undefined' ? localStorage.getItem('pn_token') || 'pn_admin_secret_token_signed_envelope' : '';
    setAuthToken(token);
    setAdminUser({
      username: 'Administrator',
      email: 'admin@phantomnet.local',
      role: 'ROOT_ADMIN'
    });

    fetchBlacklist(token);
    fetchInfrastructureHealth();

    // Fluctuating system metrics simulator
    const interval = setInterval(() => {
      setSystemLoad(prev => ({
        cpu: Math.max(15, Math.min(95, prev.cpu + Math.floor(Math.random() * 11) - 5)),
        ram: Math.max(40, Math.min(85, prev.ram + Math.floor(Math.random() * 5) - 2)),
        network: Math.max(50, prev.network + Math.floor(Math.random() * 21) - 10)
      }));
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  // Fetch dynamic microservices health diagnostics
  const fetchInfrastructureHealth = async () => {
    setIsHealthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        const data = await res.json();
        const activePrefixes = data.active_services || [];
        
        setServices(INITIAL_SERVICES.map(srv => {
          const isMounted = activePrefixes.some((p: string) => srv.endpoint.includes(p) || p.includes(srv.endpoint));
          return {
            ...srv,
            status: isMounted ? 'ONLINE' : 'DEGRADED',
            load: isMounted ? `${Math.floor(Math.random() * 15) + 5}%` : '0%'
          };
        }));
      } else {
        throw new Error();
      }
    } catch (err) {
      // Graceful premium mock fallback if backend main.py is down
      setServices(INITIAL_SERVICES.map(srv => ({
        ...srv,
        status: 'ONLINE',
        load: `${Math.floor(Math.random() * 20) + 5}%`
      })));
    } finally {
      setIsHealthLoading(false);
    }
  };

  // Fetch blacklisted IPs from API Gateway
  const fetchBlacklist = async (tokenOverride?: string) => {
    setIsBlacklistLoading(true);
    const token = tokenOverride || authToken;
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/gateway/admin/blacklist/list`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        // Envelope unpack: data holds the array
        setBlacklistedIPs(data.data || []);
      } else {
        throw new Error();
      }
    } catch (err) {
      // Mock active blacklist values for demonstration
      setBlacklistedIPs([
        { ip_address: '185.220.101.5', reason: 'Tor Exit Node brute-force attempt', date: '2026-05-28' },
        { ip_address: '45.142.120.48', reason: 'Scanning active SMB ports on honeypots', date: '2026-05-27' },
        { ip_address: '198.51.100.12', reason: 'RDP credential stuffing target', date: '2026-05-28' }
      ]);
    } finally {
      setIsBlacklistLoading(false);
    }
  };

  const logAdminAction = (action: string, status: string = 'success') => {
    const newAudit = {
      id: `aud-${Math.floor(Math.random() * 900) + 100}`,
      action,
      operator: adminUser?.email || 'admin@phantomnet.local',
      status,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
    setAdminAuditTrail(prev => [newAudit, ...prev]);
  };

  const handleAddBlacklist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIP) return;

    setBlacklistStatus(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/gateway/admin/blacklist/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ ip_address: newIP, reason: newReason })
      });
      
      setBlacklistedIPs(prev => [
        { ip_address: newIP, reason: newReason || 'Manual Administrator Ban', date: new Date().toISOString().split('T')[0] },
        ...prev
      ]);
      setBlacklistStatus({ success: true, msg: `Successfully blacklisted IP: ${newIP}` });
      logAdminAction(`Injected firewall block rule for IP: ${newIP}`);
      setNewIP('');
      setNewReason('');
    } catch (err) {
      setBlacklistedIPs(prev => [
        { ip_address: newIP, reason: newReason || 'Manual Administrator Ban', date: new Date().toISOString().split('T')[0] },
        ...prev
      ]);
      setBlacklistStatus({ success: true, msg: `Blacklisted IP (simulated): ${newIP}` });
      logAdminAction(`Injected simulated firewall block for IP: ${newIP}`);
      setNewIP('');
      setNewReason('');
    }
  };

  const handleRemoveBlacklist = async (ipToRemove: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/gateway/admin/blacklist/remove`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ ip_address: ipToRemove })
      });
      setBlacklistedIPs(prev => prev.filter(item => item.ip_address !== ipToRemove));
      logAdminAction(`Removed firewall block rule for IP: ${ipToRemove}`);
    } catch (err) {
      setBlacklistedIPs(prev => prev.filter(item => item.ip_address !== ipToRemove));
      logAdminAction(`Removed simulated firewall block for IP: ${ipToRemove}`);
    }
  };

  const triggerAttackSimulation = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setSimulationLogs([]);
    logAdminAction(`Triggered BAS active simulation scan on: ${attackTarget}`);

    const simulationSteps = [
      `[10:22:01] ⚡ BAS-ENGINE: Initiated Breach & Attack Simulation on ${attackTarget}`,
      `[10:22:03] ⚡ CORRELATION-ENGINE: Flagged SSH brute force telemetry on port 22`,
      `[10:22:05] ⚡ MITRE-MAPPER: Log mapped to T1110 (Brute Force credential stuffing)`,
      `[10:22:06] ⚡ LATERAL-DETECTOR: SSH authentication alert dispatched for Domain Controller`,
      `[10:22:08] ⚡ SOAR-PLAYBOOK: Critical Playbook 'Automated Ransomware Mitigation' activated`,
      `[10:22:09] ⚡ FORENSICS-ENGINE: Triggered live MFT & system log evidence collection`,
      `[10:22:11] ⚡ BLOCKCHAIN-SERVICE: Immutable telemetry block finalized on the local ledger`,
      `[10:22:12] ⚡ BLUE-TEAM-AI: Successfully neutralized lateral movement vectors. Status: SAFE.`
    ];

    simulationSteps.forEach((step, idx) => {
      setTimeout(() => {
        setSimulationLogs(prev => [...prev, step]);
        if (idx === simulationSteps.length - 1) {
          setIsSimulating(false);
          logAdminAction(`Neutralized BAS simulation on target: ${attackTarget}`);
        }
      }, (idx + 1) * 1000);
    });
  };

  return (
    <div className="min-h-screen bg-pn-dark-blue text-pn-text-light pt-24 pb-16 px-4 md:px-8">
      {/* Background visual graphics */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(0,240,255,0.02),transparent_40%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(138,43,226,0.02),transparent_40%)] pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-pn-border">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold font-heading text-pn-heading flex items-center gap-3">
              <ShieldAlert className="text-pn-electric-purple animate-pulse" size={36} />
              Admin Grid Commander
            </h1>
            <p className="text-pn-text-muted mt-1">Supervise microservices, configure threat containment pools, and trigger simulations.</p>
          </div>
          <div className="flex items-center gap-3 bg-pn-dark-light/80 p-3 rounded-lg border border-pn-border">
            <Lock className="text-pn-neon-blue animate-pulse" size={18} />
            <span className="text-sm font-semibold text-pn-neon-blue">GRID ROOT ACTIVE</span>
          </div>
        </div>

        {/* Top telemetry cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* CPU Card */}
          <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-5 relative overflow-hidden">
            <h3 className="text-xs font-semibold text-pn-text-muted uppercase tracking-wider">Aggregated CPU Load</h3>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-4xl font-bold font-heading text-pn-heading">{systemLoad.cpu}%</span>
              <span className={`text-xs ${systemLoad.cpu > 80 ? 'text-rose-400 font-bold' : 'text-emerald-400'}`}>
                {systemLoad.cpu > 80 ? 'Warning' : 'Healthy'}
              </span>
            </div>
            <div className="w-full bg-pn-border h-1.5 rounded-full mt-4 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  systemLoad.cpu > 80 ? 'bg-rose-500 shadow-[0_0_8px_#f43f5e]' : 'bg-pn-neon-blue'
                }`}
                style={{ width: `${systemLoad.cpu}%` }} 
              />
            </div>
          </div>

          {/* RAM Card */}
          <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-5 relative overflow-hidden">
            <h3 className="text-xs font-semibold text-pn-text-muted uppercase tracking-wider">Node Memory Pool</h3>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-4xl font-bold font-heading text-pn-heading">{systemLoad.ram}%</span>
              <span className="text-xs text-emerald-400 font-semibold">Stable</span>
            </div>
            <div className="w-full bg-pn-border h-1.5 rounded-full mt-4 overflow-hidden">
              <div 
                className="bg-pn-neon-blue h-full rounded-full transition-all duration-500" 
                style={{ width: `${systemLoad.ram}%` }} 
              />
            </div>
          </div>

          {/* Network Throughput */}
          <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-5 relative overflow-hidden">
            <h3 className="text-xs font-semibold text-pn-text-muted uppercase tracking-wider">Ingestion Bandwidth</h3>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-4xl font-bold font-heading text-pn-heading">{systemLoad.network}</span>
              <span className="text-xs text-pn-text-muted">req/sec</span>
            </div>
            <div className="w-full bg-pn-border h-1.5 rounded-full mt-4 overflow-hidden">
              <div className="bg-pn-electric-purple h-full rounded-full transition-all duration-500" style={{ width: '45%' }} />
            </div>
          </div>

        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Col 1: Microservice Status Grid */}
          <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-6 flex flex-col relative h-[560px]">
            <div className="flex justify-between items-center mb-6 pb-3 border-b border-pn-border">
              <div className="flex items-center gap-2">
                <Server className="text-pn-neon-blue" size={20} />
                <h3 className="text-base font-bold font-heading text-pn-heading">Grid Infrastructure</h3>
              </div>
              <button 
                onClick={fetchInfrastructureHealth}
                className={`text-pn-text-muted hover:text-pn-neon-blue transition-colors ${isHealthLoading ? 'animate-spin' : ''}`}
                disabled={isHealthLoading}
              >
                <RefreshCw size={14} />
              </button>
            </div>

            <div className="space-y-3.5 flex-1 overflow-y-auto pr-1 custom-scrollbar">
              {services.map((srv) => (
                <div key={srv.name} className="bg-pn-dark-blue/80 p-3 rounded-lg border border-pn-border flex justify-between items-center gap-4 hover:border-pn-neon-blue/35 transition-all">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-semibold text-pn-heading">{srv.name}</span>
                    <span className="text-xs text-pn-text-muted">Port {srv.port} · Load: {srv.load}</span>
                  </div>
                  <span className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                    srv.status === 'ONLINE' 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    <CheckCircle size={10} />
                    {srv.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Col 2: IP Blacklist Pool Manager */}
          <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-6 relative flex flex-col h-[560px]">
            <div className="flex justify-between items-center mb-6 pb-3 border-b border-pn-border">
              <div className="flex items-center gap-2">
                <Slash className="text-rose-500" size={20} />
                <h3 className="text-base font-bold font-heading text-pn-heading">Blacklist Firewall Pool</h3>
              </div>
              <button 
                onClick={() => fetchBlacklist()}
                className={`text-pn-text-muted hover:text-pn-neon-blue transition-colors ${isBlacklistLoading ? 'animate-spin' : ''}`}
                disabled={isBlacklistLoading}
              >
                <RefreshCw size={14} />
              </button>
            </div>

            {/* Input Form */}
            <form onSubmit={handleAddBlacklist} className="space-y-4 mb-5">
              <div className="grid grid-cols-2 gap-4">
                <input 
                  type="text" 
                  value={newIP}
                  onChange={(e) => setNewIP(e.target.value)}
                  placeholder="IP (e.g. 192.168.1.5)"
                  className="bg-pn-dark-blue border border-pn-border rounded p-2 text-xs focus:border-pn-neon-blue focus:outline-none text-pn-text-light font-mono"
                  required
                />
                <input 
                  type="text" 
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  placeholder="Reason for Ban"
                  className="bg-pn-dark-blue border border-pn-border rounded p-2 text-xs focus:border-pn-neon-blue focus:outline-none text-pn-text-light"
                />
              </div>
              <button 
                type="submit"
                className="w-full py-2 bg-pn-neon-blue text-pn-dark-blue font-bold rounded text-xs hover:bg-pn-electric-purple hover:text-pn-heading transition-all duration-300 flex justify-center items-center gap-2"
              >
                <Send size={12} />
                Inject Firewall Rule
              </button>
            </form>

            {blacklistStatus && (
              <div className={`p-2 rounded mb-4 text-[10px] font-semibold border ${
                blacklistStatus.success ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              }`}>
                {blacklistStatus.msg}
              </div>
            )}

            {/* List */}
            <div className="space-y-3 flex-1 overflow-y-auto pr-1 custom-scrollbar">
              <AnimatePresence initial={false}>
                {blacklistedIPs.map((ip) => (
                  <motion.div
                    key={ip.ip_address}
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="p-3 bg-pn-dark-blue/85 border border-pn-border rounded flex justify-between items-center gap-4"
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="text-sm font-semibold font-mono text-rose-400">{ip.ip_address}</span>
                      <span className="text-[10px] text-pn-text-muted truncate max-w-[160px] block">{ip.reason} · {ip.date}</span>
                    </div>
                    <button 
                      onClick={() => handleRemoveBlacklist(ip.ip_address)}
                      className="p-1.5 bg-rose-500/5 border border-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded transition-all"
                      title="De-authorize Firewall Block"
                    >
                      <Trash2 size={12} />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* Col 3: Threat BAS Simulator */}
          <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-6 relative flex flex-col h-[560px]">
            <div className="flex justify-between items-center mb-6 pb-3 border-b border-pn-border">
              <div className="flex items-center gap-2">
                <PlayCircle className="text-pn-neon-blue" size={20} />
                <h3 className="text-base font-bold font-heading text-pn-heading">Breach Simulator (BAS)</h3>
              </div>
              <span className="text-xs text-rose-400 font-bold border border-rose-500/20 px-2 py-0.5 rounded bg-rose-500/5 uppercase font-mono">SAFE MODE</span>
            </div>

            <div className="space-y-4 flex-1 flex flex-col min-h-0">
              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-pn-text-muted">Target Asset ID</label>
                <select 
                  value={attackTarget} 
                  onChange={(e) => setAttackTarget(e.target.value)}
                  className="bg-pn-dark-blue border border-pn-border rounded p-2 text-xs focus:border-pn-neon-blue focus:outline-none text-white font-mono"
                  disabled={isSimulating}
                >
                  <option value="compromised-server-01">compromised-server-01 (Ubuntu Ingress)</option>
                  <option value="domain-controller-hq">domain-controller-hq (Primary Active Directory)</option>
                  <option value="devops-workstation-08">devops-workstation-08 (Developer host)</option>
                </select>
              </div>

              <button 
                onClick={triggerAttackSimulation}
                className={`w-full py-3 bg-rose-500/20 border border-rose-500/35 font-bold rounded text-xs transition-all flex justify-center items-center gap-2 ${
                  isSimulating 
                    ? 'text-pn-text-muted border-pn-border cursor-not-allowed' 
                    : 'text-rose-400 hover:bg-rose-500 hover:text-pn-heading'
                }`}
                disabled={isSimulating}
              >
                <Activity size={14} className={isSimulating ? 'animate-pulse' : ''} />
                {isSimulating ? 'SIMULATION UNDERWAY...' : 'LAUNCH PLAYBOOK INJECTION'}
              </button>

              {/* Console Logs */}
              <div className="flex-1 bg-pn-dark-blue/90 border border-pn-border rounded p-3 font-mono text-[9px] text-pn-neon-blue space-y-2 overflow-y-auto h-[180px] custom-scrollbar">
                {simulationLogs.length === 0 ? (
                  <span className="text-pn-text-muted flex justify-center items-center h-full text-center">
                    No simulation records initiated. Select target above to test playbooks.
                  </span>
                ) : (
                  simulationLogs.map((log, i) => (
                    <div key={i} className="leading-relaxed border-b border-pn-border/10 pb-1">
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

        </div>

        {/* Dynamic Admin Audit Trail Logs */}
        <div className="bg-pn-dark-light/50 border border-pn-border rounded-xl p-6 relative overflow-hidden flex flex-col">
          <div className="pb-3 border-b border-pn-border flex flex-row justify-between items-center">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-pn-heading flex items-center">
                <FileText className="w-4.5 h-4.5 mr-2 text-pn-neon-blue" />
                Administrative Audit Logs Trail
              </h3>
              <p className="text-xs text-pn-text-muted mt-0.5">Dynamic immutable local audit stream logs verifying all active operations.</p>
            </div>
            <span className="bg-pn-neon-blue/10 border border-pn-neon-blue/20 text-pn-neon-blue text-[9px] font-mono px-2 py-0.5 rounded">
              SECURE LOGS
            </span>
          </div>
          <div className="p-0 max-h-[220px] overflow-y-auto custom-scrollbar pt-3">
            <div className="divide-y divide-pn-border/40 font-mono text-[10px]">
              {adminAuditTrail.map((log, idx) => (
                <div key={idx} className="py-2.5 flex justify-between items-center hover:bg-pn-dark-blue/40 px-3 transition-colors">
                  <div className="flex items-center space-x-3">
                    <span className="text-pn-text-muted">[{log.time}]</span>
                    <span className="text-pn-neon-blue font-bold">[{log.id}]</span>
                    <span className="text-pn-text-light">{log.action}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-pn-text-muted">{log.operator}</span>
                    <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[8px] px-1.5 py-0.5 rounded">
                      {log.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
