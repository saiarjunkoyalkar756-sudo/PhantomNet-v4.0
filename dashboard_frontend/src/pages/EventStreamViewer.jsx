import { createElement, useState } from 'react';
import {
  Activity, BadgeCheck, CalendarClock, CircleAlert, Database, FileSearch,
  Filter, LockKeyhole, Network, Search, ShieldCheck, X,
} from 'lucide-react';

const Guardrail = ({ icon: Icon, title, detail }) => (
  <div className="flex gap-3 rounded-xl border border-white/[0.07] bg-black/10 p-3.5">
    <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-[rgba(105,167,255,0.18)] bg-[rgba(105,167,255,0.08)] text-[#69a7ff]">{createElement(Icon, { size: 15 })}</div>
    <div><p className="text-sm font-medium text-slate-200">{title}</p><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div>
  </div>
);

const EventStreamViewer = () => {
  const [filtersOpen, setFiltersOpen] = useState(false);
  return (
    <div className="soc-page soc-grid">
      <div className="mx-auto max-w-[1600px]">
        <header className="mb-7 flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
          <div><p className="soc-eyebrow">EVENT EVIDENCE · Read-only analyst workspace</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-100 sm:text-4xl">Event stream</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Review tenant-scoped, authorization-checked, provenance-linked, validated and minimized observations when an approved event-evidence integration is available.</p></div>
          <div className="flex flex-wrap items-center gap-2"><span className="inline-flex items-center gap-2 rounded-full border border-white/[0.09] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400" aria-label="Governed Event-Evidence Integration Pending"><span className="h-1.5 w-1.5 rounded-full bg-slate-500" />Integration pending</span>
<button type="button" onClick={() => setFiltersOpen((open) => !open)} className="soc-focus inline-flex items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06]"><Filter size={14} /> {filtersOpen ? 'Hide constraints' : 'Review constraints'}</button></div>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Evidence status</p><p className="mt-3 text-xl font-semibold text-slate-100">Awaiting source</p></div><div className="rounded-xl border border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.08)] p-2.5 text-[#69a7ff]"><Database size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">No protected event-evidence endpoint is connected to this browser view.</p></section>
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Live transport</p><p className="mt-3 text-xl font-semibold text-slate-100">Disabled</p></div><div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-2.5 text-slate-400"><Network size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">This page does not open an unscoped WebSocket or retain a client-side event feed.</p></section>
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Browser storage</p><p className="mt-3 text-xl font-semibold text-slate-100">None</p></div><div className="rounded-xl border border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.08)] p-2.5 text-[#48e1c1]"><LockKeyhole size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">Raw observations are not persisted locally or exposed outside an authorized evidence contract.</p></section>
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Response authority</p><p className="mt-3 text-xl font-semibold text-slate-100">None</p></div><div className="rounded-xl border border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.08)] p-2.5 text-[#f6c453]"><ShieldCheck size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">Event review remains read-only and non-enforcing with no containment or response authority.</p></section>
        </div>

        {filtersOpen && <section className="mt-4 soc-card border-[rgba(105,167,255,0.16)] p-4"><div className="flex items-start gap-3"><CircleAlert size={18} className="mt-0.5 shrink-0 text-[#69a7ff]" /><div><p className="text-sm font-medium text-slate-200">Filter constraints are inactive</p><p className="mt-1 text-xs leading-5 text-slate-500">Time, source, severity, and entity filters must be evaluated server-side after authentication, tenant binding, evidence minimization, and authorization. This page does not construct client-side queries against raw telemetry.</p></div><button type="button" onClick={() => setFiltersOpen(false)} className="soc-focus ml-auto text-slate-500 hover:text-slate-200" aria-label="Close constraints"><X size={16} /></button></div></section>}

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_0.85fr]">
          <section className="soc-card overflow-hidden"><div className="flex flex-col gap-3 border-b border-white/[0.07] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="soc-eyebrow">Evidence workbench</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Authorized observations</h2></div><div className="flex items-center gap-2"><div className="flex h-9 items-center rounded-lg border border-white/[0.08] bg-black/10 px-3 text-slate-600"><Search size={15} /><span className="ml-2 text-xs">Evidence search unavailable</span></div><button type="button" disabled className="inline-flex h-9 items-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.02] px-3 text-xs font-medium text-slate-600"><CalendarClock size={14} /> Time range</button></div></div><div className="p-5"><div className="overflow-hidden rounded-xl border border-white/[0.07] bg-black/10"><div className="grid grid-cols-[1.1fr_0.8fr_0.8fr_0.7fr] gap-3 border-b border-white/[0.07] px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.11em] text-slate-600"><span>Observation</span><span>Source</span><span>Evidence state</span><span>Collected</span></div><div className="flex min-h-64 flex-col items-center justify-center px-6 text-center"><Activity size={27} className="text-slate-600" /><h3 className="mt-3 text-sm font-medium text-slate-300">No authorized event evidence is available</h3><p className="mt-2 max-w-md text-xs leading-5 text-slate-500">The prior client accepted unscoped stream messages. This rebuilt workspace remains intentionally empty until a protected tenant-scoped analyst workflow supplies validated, minimized observations with source provenance.</p></div></div></div></section>
          <aside className="space-y-4"><section className="soc-card p-5"><p className="soc-eyebrow">Evidence guardrails</p><h2 className="mt-1 text-lg font-semibold text-slate-100">What every observation needs</h2><div className="mt-5 space-y-3"><Guardrail icon={BadgeCheck} title="Provenance linkage" detail="Every displayed observation must be traceable to an authorized source and collection context." /><Guardrail icon={LockKeyhole} title="Tenant & capability scope" detail="Every lookup must validate the authenticated tenant and analyst capabilities." /><Guardrail icon={FileSearch} title="Minimized evidence" detail="The analyst view must return constrained fields, not unrestricted raw event detail." /></div></section><section className="soc-card border-[rgba(246,196,83,0.16)] bg-[linear-gradient(145deg,rgba(66,51,21,0.25),rgba(10,17,28,0.92))] p-5"><div className="flex items-center gap-2 text-[#f6c453]"><ShieldCheck size={17} /><p className="text-sm font-semibold">Read-only boundary</p></div><p className="mt-3 text-xs leading-5 text-slate-400">Event evidence can support investigation. It does not itself establish a verified detection, authorize containment, execute a response, or replace analyst judgment.</p></section></aside>
        </div>
      </div>
    </div>
  );
};

export default EventStreamViewer;
