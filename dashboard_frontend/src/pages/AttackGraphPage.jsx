import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Share2, Zap, Target, ShieldAlert } from 'lucide-react';

const AttackGraphPage = () => {
  // Mock attack path nodes
  const nodes = useMemo(() => [
    { id: 'n1', x: 100, y: 200, label: "External IP: 185.x.x.x", type: "threat", status: "source" },
    { id: 'n2', x: 300, y: 200, label: "Web Server (DMZ)", type: "asset", status: "compromised" },
    { id: 'n3', x: 500, y: 100, label: "DB Cluster (Internal)", type: "asset", status: "target" },
    { id: 'n4', x: 500, y: 300, label: "App Server (VLAN-2)", type: "asset", status: "safe" },
    { id: 'n5', x: 700, y: 200, label: "Domain Controller", type: "asset", status: "crown_jewel" },
  ], []);

  const links = useMemo(() => [
    { from: nodes[0], to: nodes[1], risk: "High" },
    { from: nodes[1], to: nodes[2], risk: "Critical" },
    { from: nodes[1], to: nodes[3], risk: "Medium" },
    { from: nodes[2], to: nodes[4], risk: "Critical" },
  ], [nodes]);

  return (
    <div className="h-full flex flex-col space-y-6">
      <PageHeader 
        title="ATTACK PATH MAPPING"
        subtitle="Predictive visualization of multi-stage threat propagation and lateral movement."
        actions={
            <div className="flex items-center space-x-2">
                <div className="px-3 py-1 rounded bg-destructive/20 border border-destructive/50 text-destructive text-[10px] font-bold animate-pulse">
                    CRITICAL PATH DETECTED
                </div>
            </div>
        }
      />

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Graph Canvas */}
        <Card className="lg:col-span-3 glass-panel border-primary/20 overflow-hidden relative">
          <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none" />
          
          <CardContent className="h-full p-0 relative flex items-center justify-center">
            <svg viewBox="0 0 800 400" className="w-full h-auto">
              {/* Draw Links */}
              {links.map((link, i) => (
                <g key={`link-${i}`}>
                   <motion.line
                    x1={link.from.x} y1={link.from.y}
                    x2={link.to.x} y2={link.to.y}
                    stroke={link.risk === 'Critical' ? '#ef4444' : '#8b5cf6'}
                    strokeWidth="2"
                    strokeDasharray="4 4"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ 
                        pathLength: 1, 
                        opacity: 1,
                        transition: { duration: 1, delay: i * 0.3 } 
                    }}
                  />
                  {/* Data Flow Pulse */}
                  <motion.circle
                    r="3"
                    fill={link.risk === 'Critical' ? '#ef4444' : '#8b5cf6'}
                    animate={{ 
                        cx: [link.from.x, link.to.x],
                        cy: [link.from.y, link.to.y],
                    }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear", delay: i * 0.3 }}
                  />
                </g>
              ))}

              {/* Draw Nodes */}
              {nodes.map((node, i) => (
                <motion.g 
                    key={node.id} 
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', delay: i * 0.2 }}
                >
                  <circle 
                    cx={node.x} cy={node.y} r="20" 
                    className={`fill-background stroke-2 ${
                        node.status === 'compromised' ? 'stroke-destructive' : 
                        node.status === 'source' ? 'stroke-secondary' : 
                        node.status === 'crown_jewel' ? 'stroke-yellow-500' : 'stroke-primary'
                    }`}
                  />
                  {node.status === 'compromised' && (
                    <motion.circle 
                        cx={node.x} cy={node.y} r="25" 
                        fill="none" stroke="#ef4444" strokeWidth="1"
                        animate={{ scale: [1, 1.3], opacity: [0.5, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  )}
                  <text 
                    x={node.x} y={node.y + 40} 
                    textAnchor="middle" 
                    className="fill-foreground text-[10px] font-mono uppercase tracking-tighter"
                  >
                    {node.label}
                  </text>
                  <g className="pointer-events-none">
                    {node.type === 'threat' ? (
                        <Zap x={node.x - 8} y={node.y - 8} size={16} className="text-secondary" />
                    ) : (
                        <Target x={node.x - 8} y={node.y - 8} size={16} className="text-primary" />
                    )}
                  </g>
                </motion.g>
              ))}
            </svg>
          </CardContent>
        </Card>

        {/* Info Panel */}
        <div className="space-y-6">
          <Card className="glass-panel border-primary/20">
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-widest flex items-center">
                <ShieldAlert className="w-4 h-4 mr-2 text-destructive" />
                BLAST RADIUS
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
               <div className="flex justify-between items-end">
                  <span className="text-[10px] text-muted-foreground">ASSETS AT RISK</span>
                  <span className="text-2xl font-bold font-mono text-destructive">82%</span>
               </div>
               <div className="w-full bg-muted h-1 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-destructive"
                    initial={{ width: 0 }}
                    animate={{ width: '82%' }}
                    transition={{ duration: 1, delay: 1 }}
                  />
               </div>
               <p className="text-[10px] text-muted-foreground leading-relaxed">
                  Compromise of the DMZ Web Server provides lateral access to the DB Cluster and internal VLANs. DC access is predicted within <span className="text-foreground font-bold">14 minutes</span>.
               </p>
            </CardContent>
          </Card>

          <Card className="glass-panel border-primary/20 flex-1">
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-widest flex items-center">
                <Share2 className="w-4 h-4 mr-2 text-primary" />
                RECOMMENDED ACTION
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
               <button className="w-full py-2 bg-destructive/10 hover:bg-destructive/20 border border-destructive/30 text-destructive text-[10px] font-bold rounded flex items-center justify-center transition-colors">
                  ISOLATE SOURCE (n2)
               </button>
               <button className="w-full py-2 bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary text-[10px] font-bold rounded flex items-center justify-center transition-colors">
                  INITIATE SNAPSHOT (n3)
               </button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AttackGraphPage;
