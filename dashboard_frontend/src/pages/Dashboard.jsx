import { createElement, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, ArrowRight, Bot, CheckCircle2, ChevronRight, ClipboardCheck,
  Clock3, Database, FileSearch, Network, RefreshCw, ShieldAlert,
  ShieldCheck, SlidersHorizontal, UsersRound,
} from 'lucide-react';
import { fetchHuntDashboardSummary } from '@/services/threatHunting.service';

const formatValue = (value) => (Number.isFinite(value) ? value.toLocaleString() : '—');

const MetricCard = ({ label, value, detail, icon: Icon, tone = 'teal' }) => {
  const tones = {
    teal: 'border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]',
    amber: 'border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.08)] text-[#f6c453]',
    blue: 'border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.08)] text-[#69a7ff]',
  };
  return (
    <section className="soc-card soc-card--interactive p-5" aria-label={label}>
      <div className="flex items-start justify-between gap-3">
        <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">{label}</p><p className="mt-3 text-3xl font-semibold tracking-tight text-slate-100">{formatValue(value)}</p></div>
        <div className={`rounded-xl border p-2.5 ${tones[tone]}`}>{createElement(Icon, { size: 19, strokeWidth: 1.8 })}</div>
      </div>
      <p className="mt-4 text-xs leading-5 text-slate-500">{detail}</p>
    </section>
  );
};

const PipelineStep = ({ icon: Icon, title, detail, status, active }) => (
  <div className="relative flex gap-3 py-2">
    <div className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${active ? 'border-[rgba(72,225,193,0.24)] bg-[rgba(72,225,193,0.1)] text-[#48e1c1]' : 'border-white/[0.08] bg-white/[0.03] text-slate-400'}`}>{createElement(Icon, { size: 15 })}</div>
    <div className="min-w-0"><div className="flex items-center justify-between gap-3"><p className="text-sm font-medium text-slate-200">{title}</p><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${active ? 'bg-[rgba(72,225,193,0.12)] text-[#48e1c1]' : 'bg-white/[0.05] text-slate-500'}`}>{status}</span></div><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div>
  </div>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadSummary = async () => {
    setRefreshing(true);
    try { const response = await fetchHuntDashboardSummary(); setSummary(response); setError(null); }
    catch { setError('The governed threat-hunting summary is currently unavailable. No operational values are inferred.'); }
    finally { setRefreshing(false); }
  };

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try { const response = await fetchHuntDashboardSummary(); if (mounted) { setSummary(response); setError(null); } }
      catch { if (mounted) setError('The governed threat-hunting summary is currently unavailable. No operational values are inferred.'); }
    };
    load();
    const interval = window.setInterval(load, 30_000);
    return () => { mounted = false; window.clearInterval(interval); };
  }, []);

  const techniques = useMemo(() => summary?.top_mitre_techniques ?? [], [summary]);
  const metrics = summary?.metrics ?? {};
  const summaryAvailable = Boolean(summary);

  return (
    <div className="soc-page soc-grid">
      <div className="mx-auto max-w-[1600px]">
        <header className="mb-7 flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
          <div><p className="soc-eyebrow">THREAT-HUNTING EVIDENCE SUMMARY · Security operations</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-100 sm:text-4xl">SOC command center</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Read-only governed summary of source-backed detection evidence, analyst work, and approval-bound response controls; it does not establish global visibility, autonomous orchestration, or response execution.</p></div>
          <div className="flex flex-wrap items-center gap-2"><span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${summaryAvailable ? 'border-[rgba(72,225,193,0.2)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]' : 'border-white/[0.09] bg-white/[0.03] text-slate-400'}`}><span className={`h-1.5 w-1.5 rounded-full ${summaryAvailable ? 'bg-[#48e1c1]' : 'bg-slate-500'}`} />{summaryAvailable ? 'Governed summary connected' : 'Awaiting governed summary'}</span><button type="button" onClick={loadSummary} className="soc-focus inline-flex items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06]" aria-label="Refresh governed threat-hunting summary"><RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} /> Refresh</button></div>
        </header>

        {error && <div className="mb-6 flex items-start gap-3 rounded-xl border border-[rgba(246,196,83,0.2)] bg-[rgba(246,196,83,0.07)] px-4 py-3 text-sm text-[#f6c453]" role="status"><ShieldAlert size={18} className="mt-0.5 shrink-0" /><p>{error}</p></div>}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Canonical detections" value={metrics.detections} detail="Evidence-backed detections reported by the connected governed summary." icon={Activity} />
          <MetricCard label="Active analyst alerts" value={metrics.active_alerts} detail="Alerts shown only when returned by the protected analyst workflow." icon={ShieldAlert} tone="amber" />
          <MetricCard label="Open investigations" value={metrics.open_cases} detail="Cases remain analyst-managed; this view does not execute response actions." icon={FileSearch} tone="blue" />
          <MetricCard label="Response posture" value={null} detail="High-impact response remains request → approval → signed audit → adapter → verification → rollback." icon={ShieldCheck} />
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.45fr_0.9fr]">
          <section className="soc-card overflow-hidden"><div className="flex flex-col justify-between gap-4 border-b border-white/[0.07] px-5 py-4 sm:flex-row sm:items-center"><div><p className="soc-eyebrow">Detection evidence</p><h2 className="mt-1 text-lg font-semibold text-slate-100">MITRE technique activity</h2></div><button type="button" onClick={() => navigate('/threat-hunting')} className="soc-focus inline-flex items-center gap-1 text-xs font-semibold text-[#48e1c1] hover:text-[#85f1d8]">Open threat hunting <ArrowRight size={14} /></button></div><div className="p-5">{techniques.length > 0 ? <div className="grid gap-3 sm:grid-cols-2">{techniques.slice(0, 6).map((item, index) => <div key={`${item.technique_id}-${index}`} className="rounded-xl border border-white/[0.07] bg-black/10 p-4"><div className="flex items-center justify-between gap-3"><span className="font-mono text-xs text-[#69a7ff]">MITRE {item.technique_id}</span><span className="text-sm font-semibold text-slate-200">{formatValue(item.count)}</span></div><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.05]"><div className="h-full rounded-full bg-gradient-to-r from-[#2c8fbe] to-[#48e1c1]" style={{ width: `${Math.min(100, 20 + (index * 13))}%` }} /></div></div>)}</div> : <div className="flex min-h-48 flex-col items-center justify-center rounded-xl border border-dashed border-white/[0.1] bg-black/10 px-6 text-center"><Network size={26} className="text-slate-600" /><h3 className="mt-3 text-sm font-medium text-slate-300">No governed technique evidence available</h3><p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">This panel intentionally stays empty until the protected summary returns evidence. It does not synthesize telemetry or AI findings.</p></div>}</div></section>

          <section className="soc-card p-5"><div className="flex items-start justify-between gap-4"><div><p className="soc-eyebrow">Response controls</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Governed containment</h2></div><ClipboardCheck size={19} className="text-[#48e1c1]" /></div><div className="mt-5 divide-y divide-white/[0.06]"><PipelineStep icon={ShieldAlert} title="Request" detail="Analyst or policy proposes a bounded defensive action." status="Required" active /><PipelineStep icon={UsersRound} title="Human approval" detail="High-impact containment is not self-approved." status="Required" active /><PipelineStep icon={ClipboardCheck} title="Signed audit" detail="The lifecycle requires a signed audit record before adapter execution." status="Required" active /><PipelineStep icon={CheckCircle2} title="Verify & rollback" detail="Verification and rollback remain part of the controlled lifecycle." status="Required" active /></div></section>
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.4fr]">
          <section className="soc-card p-5"><div className="flex items-center justify-between"><div><p className="soc-eyebrow">Operating posture</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Control-plane status</h2></div><SlidersHorizontal size={18} className="text-slate-400" /></div><div className="mt-5 space-y-3"><div className="flex items-center justify-between rounded-lg border border-white/[0.07] bg-black/10 px-3 py-3"><div className="flex items-center gap-3"><Database size={16} className="text-[#69a7ff]" /><span className="text-sm text-slate-300">Telemetry summary</span></div><span className={`text-xs font-semibold ${summaryAvailable ? 'text-[#48e1c1]' : 'text-slate-500'}`}>{summaryAvailable ? 'AVAILABLE' : 'AWAITING'}</span></div><div className="flex items-center justify-between rounded-lg border border-white/[0.07] bg-black/10 px-3 py-3"><div className="flex items-center gap-3"><Bot size={16} className="text-[#f6c453]" /><span className="text-sm text-slate-300">AI assistance</span></div><span className="text-xs font-semibold text-slate-500">ADVISORY ONLY</span></div><div className="flex items-center justify-between rounded-lg border border-white/[0.07] bg-black/10 px-3 py-3"><div className="flex items-center gap-3"><ShieldCheck size={16} className="text-[#48e1c1]" /><span className="text-sm text-slate-300">Response adapters</span></div><span className="text-xs font-semibold text-slate-500">DEPLOYMENT-GATED</span></div></div></section>

          <section className="soc-card p-5"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start"><div><p className="soc-eyebrow">Analyst workflow</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Start from evidence, not automation</h2></div><Clock3 size={19} className="text-slate-500" /></div><div className="mt-5 grid gap-3 md:grid-cols-3"><button type="button" onClick={() => navigate('/events')} className="soc-focus group rounded-xl border border-white/[0.07] bg-black/10 p-4 text-left transition hover:border-[rgba(105,167,255,0.3)] hover:bg-[rgba(105,167,255,0.05)]"><Activity size={18} className="text-[#69a7ff]" /><p className="mt-4 text-sm font-semibold text-slate-200">Review events</p><p className="mt-1 text-xs leading-5 text-slate-500">Inspect the event stream and retain source context.</p><span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#69a7ff]">Open stream <ChevronRight size={13} /></span></button><button type="button" onClick={() => navigate('/case-management')} className="soc-focus group rounded-xl border border-white/[0.07] bg-black/10 p-4 text-left transition hover:border-[rgba(72,225,193,0.3)] hover:bg-[rgba(72,225,193,0.05)]"><FileSearch size={18} className="text-[#48e1c1]" /><p className="mt-4 text-sm font-semibold text-slate-200">Investigate case</p><p className="mt-1 text-xs leading-5 text-slate-500">Keep analyst decisions tied to governed evidence.</p><span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#48e1c1]">Open cases <ChevronRight size={13} /></span></button><button type="button" onClick={() => navigate('/soar')} className="soc-focus group rounded-xl border border-white/[0.07] bg-black/10 p-4 text-left transition hover:border-[rgba(246,196,83,0.3)] hover:bg-[rgba(246,196,83,0.05)]"><ClipboardCheck size={18} className="text-[#f6c453]" /><p className="mt-4 text-sm font-semibold text-slate-200">Review response</p><p className="mt-1 text-xs leading-5 text-slate-500">Containment remains approval-bound and auditable.</p><span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#f6c453]">Open SOAR <ChevronRight size={13} /></span></button></div></section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
