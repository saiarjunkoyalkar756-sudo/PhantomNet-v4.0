import { createElement, useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import {
  Activity, BookmarkPlus, Bot, ChevronDown, CircleAlert, Database, FileSearch,
  Network, RefreshCw, Search, ShieldCheck, Sparkles, Workflow,
} from 'lucide-react';

import {
  executeHunt,
  executeSavedHunt,
  fetchAutomatedHunts,
  fetchHuntDashboardSummary,
  fetchSavedHunts,
  saveHunt,
} from '@/services/threatHunting.service';
import { analyzeAttackPath, refreshAttackGraph } from '@/services/attackPath.service';

const severityColors = {
  critical: '#f26d78',
  high: '#f5a45d',
  medium: '#f6c453',
  low: '#48e1c1',
  informational: '#69a7ff',
};

const emptyResult = {
  dataset: 'detections',
  result_count: 0,
  results: [],
  note: 'Hunts are read-only and do not dispatch containment or response actions.',
};

const MetricCard = ({ icon: Icon, label, value, detail, tone = 'blue' }) => {
  const tones = {
    blue: 'border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.08)] text-[#69a7ff]',
    teal: 'border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]',
    amber: 'border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.08)] text-[#f6c453]',
    rose: 'border-[rgba(242,109,120,0.16)] bg-[rgba(242,109,120,0.08)] text-[#f26d78]',
  };
  return (
    <section className="soc-card p-5">
      <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">{label}</p><p className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-slate-100">{value ?? '—'}</p></div><div className={`rounded-xl border p-2.5 ${tones[tone]}`}>{createElement(Icon, { size: 19 })}</div></div>
      <p className="mt-4 text-xs leading-5 text-slate-500">{detail}</p>
    </section>
  );
};

const EmptyChart = ({ title, detail }) => (
  <div className="flex h-64 flex-col items-center justify-center px-6 text-center"><Activity size={23} className="text-slate-600" /><p className="mt-3 text-sm font-medium text-slate-300">{title}</p><p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">{detail}</p></div>
);

const ThreatHuntingPage = () => {
  const [dataset, setDataset] = useState('detections');
  const [severity, setSeverity] = useState('');
  const [technique, setTechnique] = useState('');
  const [huntName, setHuntName] = useState('');
  const [results, setResults] = useState(emptyResult);
  const [summary, setSummary] = useState(null);
  const [savedHunts, setSavedHunts] = useState([]);
  const [automatedHunts, setAutomatedHunts] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [attackSource, setAttackSource] = useState('');
  const [attackTarget, setAttackTarget] = useState('');
  const [attackAnalysis, setAttackAnalysis] = useState(null);
  const [graphProjection, setGraphProjection] = useState(null);
  const [isGraphLoading, setIsGraphLoading] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);

  const filters = useMemo(() => {
    const next = [];
    if (severity) next.push({ field: 'severity', operator: 'eq', value: severity });
    if (technique && dataset === 'detections') next.push({ field: 'mitre_technique', operator: 'eq', value: technique.toUpperCase() });
    return next;
  }, [dataset, severity, technique]);

  const loadWorkspace = async ({ refresh = false } = {}) => {
    if (refresh) setIsRefreshing(true);
    try {
      const [dashboard, saved, automated] = await Promise.all([
        fetchHuntDashboardSummary(),
        fetchSavedHunts(),
        fetchAutomatedHunts(),
      ]);
      setSummary(dashboard);
      setSavedHunts(saved);
      setAutomatedHunts(automated);
      setError('');
    } catch (requestError) {
      setError(requestError.message || 'Threat-hunting evidence is currently unavailable.');
    } finally {
      if (refresh) setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  const execute = async () => {
    setIsLoading(true);
    setError('');
    try {
      setResults(await executeHunt({ dataset, filters, limit: 100 }));
    } catch (requestError) {
      setError(requestError.message || 'The governed hunt could not be completed.');
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
      setError(requestError.message || 'The saved hunt could not be created.');
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
      setError(requestError.message || 'The saved hunt could not be completed.');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshGraph = async () => {
    setIsGraphLoading(true);
    setError('');
    try {
      setGraphProjection(await refreshAttackGraph());
      setAttackAnalysis(null);
    } catch (requestError) {
      setError(requestError.message || 'Graph refresh requires analyst evidence and appropriate administrator access.');
    } finally {
      setIsGraphLoading(false);
    }
  };

  const analyzeGraph = async () => {
    if (!attackSource.trim() || !attackTarget.trim()) {
      setError('Provide both governed graph node identifiers before analyzing a path.');
      return;
    }
    setIsGraphLoading(true);
    setError('');
    try {
      setAttackAnalysis(await analyzeAttackPath({
        source_node_id: attackSource.trim(),
        target_node_id: attackTarget.trim(),
        max_hops: 4,
        max_paths: 10,
      }));
    } catch (requestError) {
      setError(requestError.message || 'No tenant-scoped evidence path is currently available. Refresh the graph after new evidence arrives.');
    } finally {
      setIsGraphLoading(false);
    }
  };

  const metrics = summary?.metrics;
  const severityData = summary?.alerts_by_severity || [];
  const mitreData = summary?.top_mitre_techniques || [];
  const hasSeverityData = severityData.some((item) => item.count > 0);
  const hasMitreData = mitreData.some((item) => item.count > 0);

  return (
    <div className="soc-page soc-grid">
      <div className="mx-auto max-w-[1600px]">
        <header className="mb-7 flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
          <div><p className="soc-eyebrow">THREAT HUNTING · Tenant-scoped analyst workspace</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-100 sm:text-4xl">Evidence-led hunt detail</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Structured, allowlisted hunts across governed detections, alerts, cases, assets, integrity findings, and evidence records. Hunt outputs are investigative evidence, not response authority.</p></div>
          <div className="flex flex-wrap items-center gap-2"><span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${summary ? 'border-[rgba(72,225,193,0.2)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]' : 'border-white/[0.09] bg-white/[0.03] text-slate-400'}`}><span className={`h-1.5 w-1.5 rounded-full ${summary ? 'bg-[#48e1c1]' : 'bg-slate-500'}`} />{summary ? 'Governed summary connected' : 'Awaiting governed summary'}</span><button type="button" onClick={() => loadWorkspace({ refresh: true })} disabled={isRefreshing} className="soc-focus inline-flex items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-50"><RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} /> Refresh</button></div>
        </header>

        {error && <div className="mb-5 flex items-start gap-3 rounded-xl border border-[rgba(246,196,83,0.22)] bg-[rgba(246,196,83,0.08)] px-4 py-3 text-sm text-[#f6c453]" role="status"><CircleAlert size={18} className="mt-0.5 shrink-0" /><p>{error}</p></div>}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={Database} label="Canonical detections" value={metrics?.detections} detail={summary ? 'Tenant-scoped detection records in the returned summary.' : 'Awaiting an authorized summary response.'} tone="blue" />
          <MetricCard icon={Activity} label="Active analyst alerts" value={metrics?.active_alerts} detail={summary ? 'Alert state is supplied by the governed summary.' : 'No alert count is shown without summary evidence.'} tone="teal" />
          <MetricCard icon={Sparkles} label="Critical alerts" value={metrics?.critical_alerts} detail={summary ? 'A summary count, not a real-time global claim.' : 'No critical-alert count is inferred client-side.'} tone="rose" />
          <MetricCard icon={FileSearch} label="Open investigations" value={metrics?.open_cases} detail={summary ? 'Tenant-owned case aggregate from the supported hunting summary.' : 'No case volume is inferred without evidence.'} tone="amber" />
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.45fr_0.8fr]">
          <section className="soc-card overflow-hidden"><div className="flex flex-col gap-3 border-b border-white/[0.07] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="soc-eyebrow">Structured hunt builder</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Constrained evidence query</h2></div><span className="inline-flex items-center gap-2 rounded-full border border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.07)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.11em] text-[#48e1c1]"><ShieldCheck size={13} /> Read-only hunt mode</span></div>
            <div className="p-5"><p className="max-w-3xl text-xs leading-5 text-slate-500">No raw query language is accepted. The service validates allowlisted filters, applies authenticated tenant scope, and returns canonical SOC records. A hunt cannot dispatch containment or a response action.</p><div className="mt-5 grid gap-3 md:grid-cols-3"><label className="block"><span className="text-xs font-medium text-slate-300">Dataset</span><select value={dataset} onChange={(event) => setDataset(event.target.value)} className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200"><option value="detections">Detections</option><option value="alerts">Alerts</option><option value="cases">Cases</option><option value="assets">Endpoint assets</option><option value="integrity">Integrity findings</option><option value="evidence">Evidence records</option></select></label><label className="block"><span className="text-xs font-medium text-slate-300">Severity</span><select value={severity} onChange={(event) => setSeverity(event.target.value)} className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200"><option value="">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option><option value="informational">Informational</option></select></label><label className="block"><span className="text-xs font-medium text-slate-300">MITRE technique</span><input value={technique} disabled={dataset !== 'detections'} onChange={(event) => setTechnique(event.target.value)} placeholder="e.g. T1071.004" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 font-mono text-sm text-slate-200 placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-40" /></label></div><div className="mt-4 flex flex-col gap-3 lg:flex-row"><button type="button" onClick={execute} disabled={isLoading} className="soc-focus inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[#48e1c1] px-4 text-sm font-semibold text-[#06121c] transition hover:bg-[#6ee9ce] disabled:cursor-not-allowed disabled:opacity-50"><Search size={15} />{isLoading ? 'Running governed hunt…' : 'Run governed hunt'}</button><div className="flex min-w-0 flex-1 gap-2"><input value={huntName} onChange={(event) => setHuntName(event.target.value)} placeholder="Name this structured hunt" className="soc-focus h-10 min-w-0 flex-1 rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200 placeholder:text-slate-600" /><button type="button" onClick={saveCurrentHunt} disabled={isLoading} className="soc-focus inline-flex h-10 items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-50"><BookmarkPlus size={14} />Save hunt</button></div></div><div className="mt-4 rounded-xl border border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.06)] px-3 py-2.5 text-xs leading-5 text-slate-400">{results.note}</div></div>
          </section>

          <aside className="soc-card p-5"><div className="flex items-start justify-between gap-3"><div><p className="soc-eyebrow">Automated templates</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Read-only hunt queue</h2></div><Bot size={18} className="text-[#69a7ff]" /></div><p className="mt-3 text-xs leading-5 text-slate-500">Templates query the same tenant-scoped evidence surface. Selecting one only displays its returned summary; it does not execute a response.</p><div className="mt-4 space-y-2">{Object.entries(automatedHunts).map(([name, hunt]) => <button key={name} type="button" onClick={() => setResults(hunt)} className="soc-focus w-full rounded-xl border border-white/[0.07] bg-black/10 p-3 text-left transition hover:border-[rgba(105,167,255,0.3)] hover:bg-[rgba(105,167,255,0.05)]"><div className="flex items-center justify-between gap-3"><p className="text-sm font-medium capitalize text-slate-200">{name.replaceAll('-', ' ')}</p><ChevronDown size={15} className="text-slate-500" /></div><p className="mt-1 text-xs text-slate-500">{hunt.result_count || 0} returned records · read-only</p></button>)}{!Object.keys(automatedHunts).length && <div className="rounded-xl border border-dashed border-white/[0.1] px-4 py-5 text-center text-xs leading-5 text-slate-500">No automated hunt summaries are available.</div>}</div></aside>
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.45fr_0.8fr]">
          <section className="soc-card overflow-hidden"><div className="flex flex-col gap-3 border-b border-white/[0.07] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="soc-eyebrow">Returned evidence</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Hunt results <span className="ml-1 text-sm font-normal text-slate-500">{results.result_count} records</span></h2></div><span className="text-xs text-slate-500">Dataset: <span className="font-mono text-slate-300">{results.dataset}</span></span></div><div className="overflow-x-auto"><table className="min-w-[700px] w-full text-left text-sm"><thead className="border-b border-white/[0.07] bg-black/10 text-[10px] font-semibold uppercase tracking-[0.11em] text-slate-500"><tr><th className="px-5 py-3">Record</th><th className="px-4 py-3">Title</th><th className="px-4 py-3">Severity</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">MITRE evidence</th><th className="px-5 py-3">Observed</th></tr></thead><tbody>{results.results.map((result, index) => <tr key={result.detection_id || result.alert_id || result.case_id || `${result.record_type}-${index}`} className="border-b border-white/[0.05] text-slate-300"><td className="px-5 py-3 font-mono text-xs text-slate-500">{result.record_type || 'record'}</td><td className="px-4 py-3 font-medium">{result.title || 'Untitled evidence record'}</td><td className="px-4 py-3"><span className="rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.08em]" style={{ backgroundColor: `${severityColors[result.severity] || '#64748b'}22`, color: severityColors[result.severity] || '#94a3b8' }}>{result.severity || 'not scored'}</span></td><td className="px-4 py-3 text-xs text-slate-500">{result.status || '—'}</td><td className="px-4 py-3 font-mono text-xs text-slate-500">{result.mitre_evidence?.map((item) => item.technique_id).join(', ') || '—'}</td><td className="px-5 py-3 text-xs text-slate-500">{result.timestamp ? new Date(result.timestamp).toLocaleString() : '—'}</td></tr>)}{!results.results.length && <tr><td colSpan="6"><div className="flex min-h-52 flex-col items-center justify-center px-6 text-center"><Search size={25} className="text-slate-600" /><p className="mt-3 text-sm font-medium text-slate-300">No hunt evidence selected</p><p className="mt-1 max-w-md text-xs leading-5 text-slate-500">Run a governed structured hunt, select a returned automated template, or run a saved hunt to inspect canonical tenant-scoped SOC records.</p></div></td></tr>}</tbody></table></div></section>
          <aside className="soc-card p-5"><p className="soc-eyebrow">Saved hunts</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Reusable investigation queries</h2><div className="mt-4 space-y-2">{savedHunts.map((hunt) => <button key={hunt.hunt_id} type="button" onClick={() => runSaved(hunt.hunt_id)} className="soc-focus w-full rounded-xl border border-white/[0.07] bg-black/10 p-3 text-left transition hover:border-[rgba(72,225,193,0.3)] hover:bg-[rgba(72,225,193,0.04)]"><p className="text-sm font-medium text-slate-200">{hunt.name}</p><p className="mt-1 text-xs text-slate-500">{hunt.dataset} · {hunt.filters.length} constrained filters</p></button>)}{!savedHunts.length && <div className="rounded-xl border border-dashed border-white/[0.1] px-4 py-5 text-center text-xs leading-5 text-slate-500">Save a structured hunt to reuse it in an authorized investigation workflow.</div>}</div></aside>
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-2"><section className="soc-card overflow-hidden"><div className="border-b border-white/[0.07] px-5 py-4"><p className="soc-eyebrow">Summary evidence</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Alert severity distribution</h2></div>{hasSeverityData ? <div className="h-64 p-3"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={severityData.filter((item) => item.count > 0)} dataKey="count" nameKey="severity" innerRadius={52} outerRadius={82} paddingAngle={3}>{severityData.filter((item) => item.count > 0).map((item) => <Cell key={item.severity} fill={severityColors[item.severity] || '#8b5cf6'} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div> : <EmptyChart title="No severity summary is available" detail="The chart is withheld until the governed summary provides tenant-scoped count data." />}</section><section className="soc-card overflow-hidden"><div className="border-b border-white/[0.07] px-5 py-4"><p className="soc-eyebrow">Summary evidence</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Top MITRE techniques</h2></div>{hasMitreData ? <div className="h-64 p-3"><ResponsiveContainer width="100%" height="100%"><BarChart data={mitreData} layout="vertical" margin={{ left: 18 }}><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="technique_id" width={80} /><Tooltip /><Bar dataKey="count" fill="#69a7ff" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div> : <EmptyChart title="No technique summary is available" detail="This chart appears only when the governed summary includes MITRE-linked tenant evidence." />}</section></div>

        <section className="mt-4 soc-card overflow-hidden"><button type="button" onClick={() => setGraphOpen((open) => !open)} className="soc-focus flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-white/[0.02]"><div className="flex items-center gap-3"><div className="rounded-xl border border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.08)] p-2 text-[#69a7ff]"><Workflow size={17} /></div><div><p className="soc-eyebrow">Bounded graph analysis</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Evidence-backed attack paths</h2></div></div><ChevronDown size={18} className={`text-slate-500 transition-transform ${graphOpen ? 'rotate-180' : ''}`} /></button>{graphOpen && <div className="border-t border-white/[0.07] p-5"><p className="max-w-4xl text-xs leading-5 text-slate-500">Tenant-scoped traversal only. Inputs must be canonical evidence node identifiers such as <code className="text-slate-300">case:&lt;id&gt;</code> and <code className="text-slate-300">asset:&lt;id&gt;</code>. This bounded graph analysis does not execute a response or containment action.</p><div className="mt-4 grid gap-3 md:grid-cols-2"><label className="block"><span className="text-xs font-medium text-slate-300">Source node</span><input value={attackSource} onChange={(event) => setAttackSource(event.target.value)} placeholder="case:&lt;case-id&gt;" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 font-mono text-sm text-slate-200 placeholder:text-slate-600" /></label><label className="block"><span className="text-xs font-medium text-slate-300">Target node</span><input value={attackTarget} onChange={(event) => setAttackTarget(event.target.value)} placeholder="asset:&lt;asset-id&gt;" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 font-mono text-sm text-slate-200 placeholder:text-slate-600" /></label></div><div className="mt-4 flex flex-wrap items-center gap-3"><button type="button" onClick={refreshGraph} disabled={isGraphLoading} className="soc-focus inline-flex h-10 items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-50"><Database size={14} />{isGraphLoading ? 'Refreshing…' : 'Refresh tenant graph'}</button><button type="button" onClick={analyzeGraph} disabled={isGraphLoading} className="soc-focus inline-flex h-10 items-center gap-2 rounded-lg bg-[#69a7ff] px-3 text-xs font-semibold text-[#06121c] transition hover:bg-[#8bbcff] disabled:cursor-not-allowed disabled:opacity-50"><Network size={14} />Analyze path</button>{graphProjection && <span className="text-xs text-slate-500">Snapshot: <span className="font-mono text-slate-300">{graphProjection.node_count}</span> nodes · <span className="font-mono text-slate-300">{graphProjection.edge_count}</span> evidence edges</span>}</div><div className="mt-4 space-y-2">{attackAnalysis?.paths?.map((path, index) => <div key={`${path.node_ids.join('-')}-${index}`} className="rounded-xl border border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.05)] p-3"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-[#69a7ff]">Path {index + 1} · risk {path.risk_score} · {path.hop_count} hops</p><span className="text-xs text-slate-500">{path.evidence_ids.length} evidence references</span></div><p className="mt-2 break-all font-mono text-xs text-slate-300">{path.node_ids.join('  →  ')}</p></div>)}{attackAnalysis && !attackAnalysis.paths?.length && <div className="rounded-xl border border-white/[0.08] bg-black/10 p-3 text-sm text-slate-500">No bounded attack path connects these tenant-owned evidence nodes.</div>}{!attackAnalysis && <div className="rounded-xl border border-white/[0.08] bg-black/10 p-3 text-sm text-slate-500">Refresh the graph to project current governed evidence, then analyze an explicit bounded path.</div>}</div></div>}</section>
      </div>
    </div>
  );
};

export default ThreatHuntingPage;
