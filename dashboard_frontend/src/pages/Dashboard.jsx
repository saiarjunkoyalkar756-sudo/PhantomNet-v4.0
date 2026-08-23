import React, { useEffect, useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { fetchHuntDashboardSummary } from '@/services/threatHunting.service';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    const fetchData = async () => {
      try {
        const response = await fetchHuntDashboardSummary();
        if (active) setSummary(response);
      } catch {
        if (active) setError('Governed threat-hunting summary is unavailable.');
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const metrics = [
    ['Canonical detections', summary?.metrics?.detections ?? '—'],
    ['Active analyst alerts', summary?.metrics?.active_alerts ?? '—'],
    ['Open investigations', summary?.metrics?.open_cases ?? '—'],
  ];

  return (
    <div className="min-h-screen">
      <PageHeader
        title="THREAT-HUNTING EVIDENCE SUMMARY"
        subtitle="Read-only governed summary; dashboard actions, global telemetry, and AI assistance require separately authorized integrations."
      />
      {error && <p className="mt-4 rounded border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
        {metrics.map(([title, value]) => (
          <Card key={title}>
            <CardHeader><CardTitle className="text-sm text-text-secondary">{title}</CardTitle></CardHeader>
            <CardContent><p className="text-3xl font-bold">{value}</p></CardContent>
          </Card>
        ))}
      </div>
      <Card className="mt-6">
        <CardHeader><CardTitle>Governed detection evidence</CardTitle></CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-text-secondary">This panel presents only the protected threat-hunting summary when available. It does not establish global visibility, autonomous orchestration, live propagation, containment, remediation, or AI decision support.</p>
          <ul className="space-y-2">
            {(summary?.top_mitre_techniques || []).map((item) => (
              <li key={item.technique_id} className="flex justify-between border-b border-border/50 py-2 text-sm">
                <span>MITRE {item.technique_id}</span><span>{item.count}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
