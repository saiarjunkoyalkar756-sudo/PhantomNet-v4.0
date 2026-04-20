import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe, Crosshair } from 'lucide-react';

const WorldAttackMap = () => {
  // SVG Coordinates for a simplified world layout
  const mapWidth = 800;
  const mapHeight = 400;

  // Mock static "Hotspots" for high-risk regions
  const hotspots = useMemo(() => [
    { id: 1, cx: 150, cy: 120, label: "North America", risk: "High" },
    { id: 2, cx: 420, cy: 110, label: "Europe", risk: "Medium" },
    { id: 3, cx: 650, cy: 150, label: "East Asia", risk: "Critical" },
    { id: 4, cx: 450, cy: 250, label: "Africa", risk: "Low" },
    { id: 5, cx: 200, cy: 280, label: "South America", risk: "Medium" }
  ], []);

  // Mock "Attack Vectors" (curved lines)
  const attacks = useMemo(() => [
    { id: 'a1', from: hotspots[2], to: hotspots[0], delay: 0 },
    { id: 'a2', from: hotspots[1], to: hotspots[2], delay: 1.5 },
    { id: 'a3', from: hotspots[0], to: hotspots[4], delay: 0.8 },
  ], [hotspots]);

  return (
    <Card className="h-[450px] flex flex-col glass-panel overflow-hidden relative border-primary/20 bg-[#0a0c14]">
      <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none" />
      
      <CardHeader className="z-10 bg-background/50 backdrop-blur-sm border-b border-border/50">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Globe className="w-5 h-5 text-primary animate-pulse" />
            <span className="text-sm font-bold tracking-widest text-glow-primary">LIVE GLOBAL THREAT MAP</span>
          </div>
          <div className="flex items-center space-x-4 text-[10px] text-muted-foreground font-mono">
            <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-destructive mr-1 animate-pulse" /> CRITICAL</span>
            <span className="flex items-center"><span className="w-2 h-2 rounded-full bg-secondary mr-1" /> MEDIUM</span>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 p-0 relative overflow-hidden flex items-center justify-center">
        <svg 
            viewBox={`0 0 ${mapWidth} ${mapHeight}`} 
            className="w-full h-auto opacity-80"
            style={{ filter: 'drop-shadow(0 0 20px rgba(139, 92, 246, 0.15))' }}
        >
          {/* Background Map - Simplified "Dots" representing the world */}
          <defs>
            <radialGradient id="hotspotGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.8" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Random background dots for mapping feel */}
          {Array.from({ length: 150 }).map((_, i) => (
            <circle 
              key={i}
              cx={Math.random() * mapWidth}
              cy={Math.random() * mapHeight}
              r={1}
              fill="#1e293b"
              opacity={0.3}
            />
          ))}

          {/* Draw Attack Vectors (Curved Lines) */}
          {attacks.map((attack) => {
            const midX = (attack.from.cx + attack.to.cx) / 2;
            const midY = Math.min(attack.from.cy, attack.to.cy) - 50; // Curve up
            const path = `M ${attack.from.cx} ${attack.from.cy} Q ${midX} ${midY} ${attack.to.cx} ${attack.to.cy}`;
            
            return (
              <g key={attack.id}>
                <motion.path
                  d={path}
                  fill="none"
                  stroke="rgba(139, 92, 246, 0.3)"
                  strokeWidth="1"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ 
                    pathLength: 1, 
                    opacity: [0, 1, 0],
                    transition: { 
                        duration: 3, 
                        delay: attack.delay, 
                        repeat: Infinity,
                        repeatDelay: 2
                    } 
                  }}
                />
                {/* Attack Head Indicator */}
                <motion.circle
                  r="2"
                  fill="#8b5cf6"
                  initial={{ offset: 0 }}
                  animate={{ 
                    cx: [attack.from.cx, attack.to.cx],
                    cy: [attack.from.cy, attack.to.cy],
                    transition: { duration: 3, delay: attack.delay, repeat: Infinity, repeatDelay: 2 } 
                  }}
                  style={{ filter: 'drop-shadow(0 0 5px #8b5cf6)' }}
                />
              </g>
            );
          })}

          {/* Draw Hotspots */}
          {hotspots.map((spot) => (
            <g key={spot.id}>
              {/* Pulsing ring */}
              <motion.circle
                cx={spot.cx}
                cy={spot.cy}
                r="15"
                fill="none"
                stroke={spot.risk === 'Critical' ? '#ef4444' : spot.risk === 'High' ? '#f59e0b' : '#3b82f6'}
                strokeWidth="1"
                initial={{ scale: 0.5, opacity: 0.8 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              {/* Core dot */}
              <circle
                cx={spot.cx}
                cy={spot.cy}
                r="4"
                className={
                    spot.risk === 'Critical' ? 'text-destructive fill-current' : 
                    spot.risk === 'High' ? 'text-secondary fill-current' : 'text-primary fill-current'
                }
                style={{ filter: 'drop-shadow(0 0 10px currentColor)' }}
              />
              <text 
                x={spot.cx} 
                y={spot.cy + 20} 
                textAnchor="middle" 
                className="text-[8px] font-mono fill-muted-foreground uppercase"
              >
                {spot.label}
              </text>
            </g>
          ))}
        </svg>

        {/* Legend / Stats overlay */}
        <div className="absolute bottom-4 left-4 p-3 glass-panel rounded-lg border-primary/10 font-mono text-[9px] space-y-1">
          <div className="flex items-center text-text-secondary">
             <Crosshair size={10} className="mr-2 text-primary" />
             LATENCY: <span className="text-primary ml-1">42MS</span>
          </div>
          <div className="flex items-center text-text-secondary">
             <Crosshair size={10} className="mr-2 text-primary" />
             ACTIVE THREATS: <span className="text-destructive ml-1">1,204</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default WorldAttackMap;
