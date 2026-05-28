// phantomnet-website/app/user/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Terminal, 
  Cpu, 
  Key, 
  Wifi, 
  RefreshCw, 
  CheckCircle, 
  AlertTriangle, 
  User, 
  Activity, 
  Copy, 
  Lock, 
  Unlock 
} from 'lucide-react';

// Simulated telemetry events
const INITIAL_LOGS = [
  { id: 1, type: 'INFO', service: 'IAM-SERVICE', msg: 'User login authorized via Multi-Factor Authentication', time: '10:45:12' },
  { id: 2, type: 'WARNING', service: 'DFIR-TOOLKIT', msg: 'Suspicious memory structure flagged on node-112', time: '10:42:05' },
  { id: 3, type: 'SECURITY', service: 'HONEYPOT-SERVICE', msg: 'Port scan detected on SMB Honeypot from 192.168.1.142', time: '10:39:58' },
  { id: 4, type: 'INFO', service: 'BLOCKCHAIN-AUDIT', msg: 'Audit event ledger successfully compiled and signed', time: '10:30:15' },
];

export default function UserPortal() {
  const [logs, setLogs] = useState(INITIAL_LOGS);
  const [postureScore, setPostureScore] = useState(94);
  const [honeypotsActive, setHoneypotsActive] = useState(true);
  const [securityToken, setSecurityToken] = useState('pn_tok_8f9a2e3b5d1c470a92f8b5...');
  const [isCopied, setIsCopied] = useState(false);
  const [cryptoAgility, setCryptoAgility] = useState<any>(null);
  const [isLoadingCrypto, setIsLoadingCrypto] = useState(false);

  // Fetch real crypto-agility metadata from Gateway
  const fetchCryptoAgility = async () => {
    setIsLoadingCrypto(true);
    try {
      const res = await fetch('http://localhost:8001/api/security/audit-crypto-agility');
      if (res.ok) {
        const data = await res.json();
        setCryptoAgility(data);
      } else {
        throw new Error('Fallback to local simulation');
      }
    } catch (err) {
      // Simulate real-time cryptographic audit fallback
      setCryptoAgility({
        gateway: { status: "SECURE", protocol: "Kyber-1024-Post-Quantum", bits_of_security: 256 },
        iam_service: { status: "VULNERABLE", protocol: "RSA-4096 (Shor-Vulnerable)", bits_of_security: 128 },
        agent_protocol: { status: "VULNERABLE", protocol: "ECDSA-P384 (Shor-Vulnerable)", bits_of_security: 192 }
      });
    } finally {
      setIsLoadingCrypto(false);
    }
  };

  useEffect(() => {
    fetchCryptoAgility();

    // Stream logs periodically to simulate real-time socket/data feed
    const interval = setInterval(() => {
      const events = [
        { id: Date.now(), type: 'INFO', service: 'EVENT-STREAM', msg: 'Log buffer flushed to Postgres audit sink', time: new Date().toTimeString().split(' ')[0] },
        { id: Date.now() + 1, type: 'SECURITY', service: 'LATERAL-DETECTOR', msg: 'Successful SSH authentication from authorized orchestration IP', time: new Date().toTimeString().split(' ')[0] },
        { id: Date.now() + 2, type: 'WARNING', service: 'COMPLIANCE', msg: 'ISO27001 scan reported 2 patch recommendations', time: new Date().toTimeString().split(' ')[0] },
      ];
      const randomEvent = events[Math.floor(Math.random() * events.length)];
      setLogs(prev => [randomEvent, ...prev.slice(0, 5)]);
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  const generateNewToken = () => {
    const chars = 'abcdef0123456789';
    let newToken = 'pn_tok_';
    for (let i = 0; i < 24; i++) {
      newToken += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setSecurityToken(newToken + '...');
    setIsCopied(false);
    
    // Add event log
    setLogs(prev => [
      { id: Date.now(), type: 'INFO', service: 'IAM-SERVICE', msg: 'Regenerated ephemeral User Security Handshake Token', time: new Date().toTimeString().split(' ')[0] },
      ...prev
    ]);
  };

  const copyTokenToClipboard = () => {
    navigator.clipboard.writeText(securityToken.replace('...', ''));
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-pn-dark-blue text-pn-text-light pt-24 pb-16 px-4 md:px-8">
      {/* Background radial effects */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(0,240,255,0.03),transparent_40%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(138,43,226,0.03),transparent_40%)] pointer-events-none" />

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 pb-6 border-b border-pn-border">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold font-heading text-pn-heading flex items-center gap-3">
              <Shield className="text-pn-neon-blue" size={36} />
              User Shield Portal
            </h1>
            <p className="text-pn-text-muted mt-1">Manage endpoint posture, honeypot defenses, and quantum credentials.</p>
          </div>
          <div className="flex items-center gap-4 bg-pn-dark-light/80 p-3 rounded-lg border border-pn-border">
            <div className="flex items-center gap-2">
              <User className="text-pn-electric-purple" />
              <div>
                <div className="text-sm font-semibold text-pn-heading">Enterprise User</div>
                <div className="text-xs text-pn-text-muted">ID: client_node_140b</div>
              </div>
            </div>
          </div>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Column 1 & 2: Main Telemetry */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Row 1: Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Posture Card */}
              <div className="bg-pn-dark-light/55 border border-pn-border p-6 rounded-xl relative overflow-hidden">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-pn-neon-blue/10 rounded-lg text-pn-neon-blue">
                    <Activity size={24} />
                  </div>
                  <span className="text-xs font-semibold px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-md border border-emerald-500/20">Optimal</span>
                </div>
                <h3 className="text-sm font-semibold text-pn-text-muted uppercase tracking-wider">Device Posture</h3>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-4xl font-bold font-heading text-pn-heading">{postureScore}%</span>
                  <span className="text-xs text-emerald-400">Excellent</span>
                </div>
                <div className="w-full bg-pn-border h-1.5 rounded-full mt-4 overflow-hidden">
                  <div className="bg-pn-neon-blue h-full rounded-full" style={{ width: `${postureScore}%` }} />
                </div>
              </div>

              {/* Honeypots Active */}
              <div className="bg-pn-dark-light/55 border border-pn-border p-6 rounded-xl relative overflow-hidden">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-pn-electric-purple/10 rounded-lg text-pn-electric-purple">
                    <Wifi size={24} />
                  </div>
                  <button 
                    onClick={() => setHoneypotsActive(!honeypotsActive)}
                    className={`text-xs font-semibold px-3 py-1 rounded-md border transition-all duration-300 ${
                      honeypotsActive 
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20' 
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/20'
                    }`}
                  >
                    {honeypotsActive ? 'Disable' : 'Enable'}
                  </button>
                </div>
                <h3 className="text-sm font-semibold text-pn-text-muted uppercase tracking-wider">Decoy Honeypots</h3>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-bold font-heading text-pn-heading">
                    {honeypotsActive ? 'ACTIVE' : 'OFFLINE'}
                  </span>
                </div>
                <p className="text-xs text-pn-text-muted mt-4">
                  {honeypotsActive ? '12 decoy listeners mapping scanning behavior' : 'Network telemetry mapping disabled'}
                </p>
              </div>

              {/* Security Token Card */}
              <div className="bg-pn-dark-light/55 border border-pn-border p-6 rounded-xl relative overflow-hidden">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-pn-neon-blue/10 rounded-lg text-pn-neon-blue">
                    <Key size={24} />
                  </div>
                  <button 
                    onClick={generateNewToken}
                    className="p-1.5 hover:bg-pn-border rounded-lg text-pn-text-muted hover:text-pn-neon-blue transition-all"
                    title="Regenerate Token"
                  >
                    <RefreshCw size={16} />
                  </button>
                </div>
                <h3 className="text-sm font-semibold text-pn-text-muted uppercase tracking-wider">Handshake Token</h3>
                <div className="flex items-center justify-between bg-pn-dark-blue/80 px-3 py-1.5 rounded border border-pn-border mt-3">
                  <span className="text-xs font-mono text-pn-neon-blue truncate pr-2">{securityToken}</span>
                  <button onClick={copyTokenToClipboard} className="text-pn-text-muted hover:text-pn-heading transition-colors">
                    {isCopied ? <CheckCircle size={14} className="text-emerald-400" /> : <Copy size={14} />}
                  </button>
                </div>
                <p className="text-[10px] text-pn-text-muted mt-3">Rotates every 60m for Zero-Trust session validation.</p>
              </div>

            </div>

            {/* Live Terminal & Logs */}
            <div className="bg-pn-dark-light/55 border border-pn-border rounded-xl p-6 relative">
              <div className="flex justify-between items-center mb-4 border-b border-pn-border pb-3">
                <div className="flex items-center gap-2">
                  <Terminal className="text-pn-neon-blue animate-pulse" size={20} />
                  <h3 className="text-lg font-bold font-heading text-pn-heading">Security Telemetry Logs</h3>
                </div>
                <span className="flex items-center gap-1.5 text-xs text-pn-neon-blue">
                  <span className="h-2 w-2 rounded-full bg-pn-neon-blue animate-ping" />
                  Live Event Ingestor
                </span>
              </div>

              <div className="font-mono text-xs space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                <AnimatePresence initial={false}>
                  {logs.map((log) => (
                    <motion.div
                      key={log.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3 bg-pn-dark-blue/85 border-l-2 rounded-r border-pn-border hover:border-pn-neon-blue hover:bg-pn-dark-blue transition-all duration-300 flex items-start justify-between gap-4"
                      style={{
                        borderLeftColor: 
                          log.type === 'SECURITY' ? '#e74c3c' : 
                          log.type === 'WARNING' ? '#f39c12' : '#00F0FF'
                      }}
                    >
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            log.type === 'SECURITY' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                            log.type === 'WARNING' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                            'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                          }`}>
                            {log.type}
                          </span>
                          <span className="text-pn-text-muted text-[10px]">{log.service}</span>
                        </div>
                        <p className="text-pn-text-light mt-1">{log.msg}</p>
                      </div>
                      <span className="text-pn-text-muted shrink-0 text-[10px]">{log.time}</span>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>

          </div>

          {/* Column 3: Crypto Agility & Quantum Trust */}
          <div className="space-y-8">
            <div className="bg-pn-dark-light/55 border border-pn-border rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-[radial-gradient(circle_at_center,rgba(138,43,226,0.1),transparent_70%)] pointer-events-none" />
              
              <div className="flex justify-between items-center mb-6 pb-3 border-b border-pn-border">
                <div className="flex items-center gap-2">
                  <Cpu className="text-pn-electric-purple" size={20} />
                  <h3 className="text-lg font-bold font-heading text-pn-heading">Crypto-Agility Audit</h3>
                </div>
                <button 
                  onClick={fetchCryptoAgility} 
                  className={`text-pn-text-muted hover:text-pn-neon-blue transition-colors ${isLoadingCrypto ? 'animate-spin' : ''}`}
                  disabled={isLoadingCrypto}
                >
                  <RefreshCw size={16} />
                </button>
              </div>

              <div className="space-y-5">
                {cryptoAgility ? (
                  Object.keys(cryptoAgility).map((layer) => {
                    const audit = cryptoAgility[layer];
                    const isSecure = audit.status === 'SECURE';
                    return (
                      <div key={layer} className="bg-pn-dark-blue/80 p-4 rounded-lg border border-pn-border flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-semibold capitalize text-pn-text-muted">{layer.replace('_', ' ')}</span>
                          <span className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded border ${
                            isSecure 
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          }`}>
                            {isSecure ? <Lock size={10} /> : <Unlock size={10} />}
                            {audit.status}
                          </span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-sm font-semibold text-pn-heading">{audit.protocol}</span>
                          <span className="text-[10px] text-pn-text-muted">{audit.bits_of_security}-bit symmetric strength equivalent</span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center py-6 text-pn-text-muted text-xs">
                    No crypto audit logs fetched.
                  </div>
                )}

                <div className="p-4 bg-pn-neon-blue/5 border border-pn-neon-blue/20 rounded-lg flex gap-3">
                  <AlertTriangle className="text-pn-neon-blue shrink-0" size={20} />
                  <div>
                    <h4 className="text-xs font-bold text-pn-heading">Post-Quantum Transition Warning</h4>
                    <p className="text-[10px] text-pn-text-muted mt-1">
                      2 core components rely on Shor-vulnerable classical asymmetric cryptography. Apply PQC Kyber patching immediately.
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
