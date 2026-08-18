import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, BookmarkPlus, Bot, Database, Search, ShieldCheck, Sparkles } from 'lucide-react';

import PageHeader from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  executeHunt,
  executeSavedHunt,
  fetchAutomatedHunts,
  fetchHuntDashboardSummary,
  fetchSavedHunts,
  saveHunt,
} from '@/services/threatHunting.service';

const severityColors = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  informational: '#38bdf8',
};

const defaultResult = {
  dataset: 'detections',
  result_count: 0,
  results: [],
  note: 'Hunts are read-only and do not dispatch containment or response actions.',
};

const ThreatHuntingPage = () => {
  const [dataset, setDataset] = useState('detections');
  const [severity, setSeverity] = useState('');
  const [technique, setTechnique] = useState('');
  const [huntName, setHuntName] = useState('');
  const [results, setResults] = useState(defaultResult);
  const [summary, setSummary] = useState(null);
  const [savedHunts, setSavedHunts] = useState([]);
  const [automatedHunts, setAutomatedHunts] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const filters = useMemo(() => {
    const next = [];
    if (severity) next.push({ field: 'severity', operator: 'eq', value: severity });
    if (technique && dataset === 'detections') next.push({ field: 'mitre_technique', operator: 'eq', value: technique.toUpperCase() });
    return next;
  }, [dataset, severity, technique]);

  const loadWorkspace = async () => {
    try {
      const [dashboard, saved, automated] = await Promise.all([
        fetchHuntDashboardSummary(),
        fetchSavedHunts(),
        fetchAutomatedHunts(),
      ]);
      setSummary(dashboard);
      setSavedHunts(saved);
      setAutomatedHunts(automated);
    } catch (requestError) {
      setError(requestError.message || 'Threat-hunting data is currently unavailable.');
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  const execute = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await executeHunt({ dataset, filters, limit: 100 });
      setResults(response);
    } catch (requestError) {
      setError(requestError.message || 'Hunt execution failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const saveCurrentHunt = async () => {
    if (!huntName.trim()) {
      setError('Provide a saved-hunt name before saving this structured query.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await saveHunt({
        name: huntName.trim(),
        description: 'Analyst-defined structured hunt.',
        dataset,
        filters,
        limit: 100,
      });
      setHuntName('');
      setSavedHunts(await fetchSavedHunts());
    } catch (requestError) {
      setError(requestError.message || 'Saved hunt could not be created.');
    } finally {
      setIsLoading(false);
    }
  };

  const runSaved = async (huntId) => {
    setIsLoading(true);
    setError('');
    try {
      setResults(await executeSavedHunt(huntId));
    } catch (requestError) {
      setError(requestError.message || 'Saved hunt execution failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const metrics = summary?.metrics || { detections: 0, active_alerts: 0, critical_alerts: 0, open_cases: 0 };
  const severityData = summary?.alerts_by_severity || [];
  const mitreData = summary?.top_mitre_techniques || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-6"
    >
      <PageHeader
        title="THREAT HUNTING WORKSPACE"
        subtitle="Tenant-scoped, structured hunts across governed detections, alerts, and investigation cases."
        actions={
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-400">
            <ShieldCheck className="h-4 w-4" />
            READ-ONLY HUNT MODE
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ['Canonical detections', metrics.detections, Database],
          ['Active analyst alerts', metrics.active_alerts, Activity],
          ['Critical alerts', metrics.critical_alerts, Sparkles],
          ['Open investigations', metrics.open_cases, ShieldCheck],
        ].map(([label, value, Icon]) => (
          <Card key={label} className="border-border/60 bg-card/70">
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
                <p className="mt-2 text-3xl font-bold tracking-tight">{value}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-3 text-primary"><Icon className="h-5 w-5" /></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2 border-border/60 bg-card/70">
          <CardHeader className="border-b border-border/50">
            <CardTitle className="flex items-center gap-2 text-base"><Search className="h-4 w-4 text-primary" /> Governed hunt builder</CardTitle>
            <p className="text-sm text-muted-foreground">No raw query language is accepted. Filters are allowlisted and executed only against your tenant’s SOC records.</p>
          </CardHeader>
          <CardContent className="space-y-4 pt-5">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2"><Label htmlFor="hunt-dataset">Dataset</Label><select id="hunt-dataset" value={dataset} onChange={(event) => setDataset(event.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option value="detections">Detections</option><option value="alerts">Alerts</option><option value="cases">Cases</option></select></div>
              <div className="space-y-2"><Label htmlFor="hunt-severity">Severity</Label><select id="hunt-severity" value={severity} onChange={(event) => setSeverity(event.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option value="">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option><option value="informational">Informational</option></select></div>
              <div className="space-y-2"><Label htmlFor="hunt-mitre">MITRE technique</Label><Input id="hunt-mitre" disabled={dataset !== 'detections'} value={technique} onChange={(event) => setTechnique(event.target.value)} placeholder="e.g. T1071.004" /></div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button onClick={execute} disabled={isLoading}><Search className="mr-2 h-4 w-4" />{isLoading ? 'Hunting…' : 'Run hunt'}</Button>
              <div className="flex min-w-[260px] flex-1 gap-2"><Input value={huntName} onChange={(event) => setHuntName(event.target.value)} placeholder="Name this hunt" /><Button variant="outline" onClick={saveCurrentHunt} disabled={isLoading}><BookmarkPlus className="mr-2 h-4 w-4" />Save</Button></div>
            </div>
            <div className="rounded-md border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">{results.note}</div>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card/70">
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Bot className="h-4 w-4 text-primary" /> Automated hunt queue</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(automatedHunts).map(([name, hunt]) => (
              <button key={name} onClick={() => setResults(hunt)} className="w-full rounded-lg border border-border/60 bg-background/40 p-3 text-left transition hover:border-primary/50 hover:bg-primary/5">
                <p className="text-sm font-semibold">{name.replaceAll('-', ' ')}</p>
                <p className="mt-1 text-xs text-muted-foreground">{hunt.result_count || 0} current findings · read-only</p>
              </button>
            ))}
            {!Object.keys(automatedHunts).length && <p className="text-sm text-muted-foreground">No automated hunt summaries available.</p>}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="border-border/60 bg-card/70"><CardHeader><CardTitle className="text-base">Alert severity distribution</CardTitle></CardHeader><CardContent className="h-64"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={severityData.filter((item) => item.count > 0)} dataKey="count" nameKey="severity" innerRadius={55} outerRadius={84} paddingAngle={3}>{severityData.filter((item) => item.count > 0).map((item) => <Cell key={item.severity} fill={severityColors[item.severity] || '#8b5cf6'} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></CardContent></Card>
        <Card className="border-border/60 bg-card/70"><CardHeader><CardTitle className="text-base">Top MITRE techniques</CardTitle></CardHeader><CardContent className="h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={mitreData} layout="vertical" margin={{ left: 18 }}><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="technique_id" width={80} /><Tooltip /><Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></CardContent></Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2 border-border/60 bg-card/70"><CardHeader><CardTitle className="text-base">Hunt results <span className="ml-2 text-sm font-normal text-muted-foreground">{results.result_count} findings</span></CardTitle></CardHeader><CardContent><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-border/50 text-xs uppercase text-muted-foreground"><tr><th className="p-3">Record</th><th className="p-3">Title</th><th className="p-3">Severity</th><th className="p-3">Status</th><th className="p-3">MITRE</th><th className="p-3">Time</th></tr></thead><tbody>{results.results.map((result) => <tr key={result.detection_id || result.alert_id || result.case_id} className="border-b border-border/30"><td className="p-3 font-mono text-xs text-muted-foreground">{result.record_type}</td><td className="p-3 font-medium">{result.title}</td><td className="p-3"><span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ backgroundColor: `${severityColors[result.severity] || '#64748b'}22`, color: severityColors[result.severity] || '#94a3b8' }}>{result.severity}</span></td><td className="p-3 text-muted-foreground">{result.status}</td><td className="p-3 font-mono text-xs">{result.mitre_evidence?.map((item) => item.technique_id).join(', ') || '—'}</td><td className="p-3 text-xs text-muted-foreground">{result.timestamp ? new Date(result.timestamp).toLocaleString() : '—'}</td></tr>)}{!results.results.length && <tr><td colSpan="6" className="p-8 text-center text-muted-foreground">Run a governed hunt or select an automated template to inspect canonical SOC records.</td></tr>}</tbody></table></div></CardContent></Card>
        <Card className="border-border/60 bg-card/70"><CardHeader><CardTitle className="text-base">Saved hunts</CardTitle></CardHeader><CardContent className="space-y-2">{savedHunts.map((hunt) => <button key={hunt.hunt_id} onClick={() => runSaved(hunt.hunt_id)} className="w-full rounded-md border border-border/60 p-3 text-left transition hover:border-primary/50 hover:bg-primary/5"><p className="text-sm font-medium">{hunt.name}</p><p className="mt-1 text-xs text-muted-foreground">{hunt.dataset} · {hunt.filters.length} filters</p></button>)}{!savedHunts.length && <p className="text-sm text-muted-foreground">Save a structured hunt to reuse it across your investigation workflow.</p>}</CardContent></Card>
      </div>
    </motion.div>
  );
};

export default ThreatHuntingPage;
