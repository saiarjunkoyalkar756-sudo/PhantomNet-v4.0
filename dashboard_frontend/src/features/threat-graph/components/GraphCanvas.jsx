import React from 'react';
import { GitGraph } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const GraphCanvas = () => (
  <Card className="h-full flex flex-col">
    <CardContent className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-2xl text-center">
        <GitGraph size={52} className="mx-auto text-primary" />
        <h2 className="mt-4 text-lg font-semibold text-primary">Governed Attack-Path Visualization Integration Pending</h2>
        <p className="mt-3 text-sm text-text-secondary leading-6">
          This dashboard does not display an attack-path graph, relationship data, asset exposure, threat routes, or interactive graph controls. The previous canvas was a placeholder and could be mistaken for a live investigation view.
        </p>
        <p className="mt-3 text-sm text-text-secondary leading-6">
          The separately protected attack-path API remains the only supported analysis boundary. Any future dashboard visualization must query tenant-scoped, authorized, provenance-linked results and must distinguish graph hypotheses from verified evidence before it is exposed as operational capability.
        </p>
      </div>
    </CardContent>
  </Card>
);

export default GraphCanvas;
