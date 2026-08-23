import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe } from 'lucide-react';

const WorldAttackMap = () => (
  <Card className="h-[450px] flex flex-col glass-panel overflow-hidden relative border-primary/20 bg-[#0a0c14]">
    <CardHeader className="z-10 bg-background/50 backdrop-blur-sm border-b border-border/50">
      <CardTitle className="flex items-center space-x-2">
        <Globe className="w-5 h-5 text-primary" />
        <span className="text-sm font-bold tracking-widest text-glow-primary">GLOBAL EVIDENCE VISUALIZATION</span>
      </CardTitle>
    </CardHeader>
    <CardContent className="flex-1 p-6 flex items-center">
      <div>
        <h2 className="text-lg font-semibold text-primary">Governed Global-Evidence Visualization Integration Pending</h2>
        <p className="mt-3 text-sm text-text-secondary leading-6">
          This dashboard does not present animated attack vectors, regional risk labels, latency measurements, active-threat counts, or global threat activity. The prior map used mock hotspots and generated visual effects that could be mistaken for observed telemetry or verified geographic intelligence.
        </p>
        <p className="mt-3 text-sm text-text-secondary leading-6">
          Any future visualization must consume tenant-scoped, provenance-linked and minimized evidence through a protected analyst workflow; distinguish source geography from verified attacker attribution; disclose data currency and availability; and remain read-only, advisory, and non-enforcing. It must not imply live global visibility, threat-detection efficacy, automatic containment, or response execution.
        </p>
      </div>
    </CardContent>
  </Card>
);

export default WorldAttackMap;
