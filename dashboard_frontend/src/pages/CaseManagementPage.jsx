import { createElement, useState } from 'react';
import {
  BadgeCheck, Bot, CheckCircle2, ClipboardCheck, FileSearch, LockKeyhole,
  Network, Plus, ShieldAlert, ShieldCheck, UserCheck, X,
} from 'lucide-react';

const LifecycleRow = ({ icon: Icon, title, detail, state, tone = 'slate' }) => {
  const styles = {
    slate: 'border-white/[0.08] bg-white/[0.03] text-slate-400',
    teal: 'border-[rgba(72,225,193,0.18)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]',
    amber: 'border-[rgba(246,196,83,0.18)] bg-[rgba(246,196,83,0.08)] text-[#f6c453]',
  };
  return (
    <div className="flex gap-3 py-3"><div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${styles[tone]}`}>{createElement(Icon, { size: 15 })}</div>
<div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-3"><p className="text-sm font-medium text-slate-200">{title}</p><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${tone === 'teal' ? 'bg-[rgba(72,225,193,0.11)] text-[#48e1c1]' : tone === 'amber' ? 'bg-[rgba(246,196,83,0.11)] text-[#f6c453]' : 'bg-white/[0.05] text-slate-500'}`}>{state}</span></div><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div></div>
  );
};

const CaseManagementPage = () => {
  const [policyOpen, setPolicyOpen] = useState(false);
  return (
    <div className="soc-page soc-grid">
      <div className="mx-auto max-w-[1600px]">
        <header className="mb-7 flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
          <div><p className="soc-eyebrow">INCIDENT CASE MANAGEMENT · Governed analyst workflow</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-100 sm:text-4xl">Case workspace</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Governed Case-Lifecycle Integration Pending: review case lifecycle boundaries, triage context, and response controls without exposing the retired legacy case surface or direct playbook execution.</p></div>
          <div className="flex flex-wrap items-center gap-2"><span className="inline-flex items-center gap-2 rounded-full border border-white/[0.09] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400"><span className="h-1.5 w-1.5 rounded-full bg-slate-500" />Case discovery pending</span><button type="button" onClick={() => setPolicyOpen((open) => !open)} className="soc-focus inline-flex items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06]"><ShieldCheck size={14} /> {policyOpen ? 'Hide policy' : 'Review policy'}</button></div>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Case discovery</p><p className="mt-3 text-xl font-semibold text-slate-100">Unavailable</p></div><div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-2.5 text-slate-400"><FileSearch size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">This page does not list cases until a tenant-scoped discovery endpoint is separately exposed.</p></section>
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">State transitions</p><p className="mt-3 text-xl font-semibold text-slate-100">Protected</p></div><div className="rounded-xl border border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.08)] p-2.5 text-[#48e1c1]"><BadgeCheck size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">Status updates require an authenticated tenant and the supported analyst capability boundary.</p></section>
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Playbook posture</p><p className="mt-3 text-xl font-semibold text-slate-100">Approval-bound</p></div><div className="rounded-xl border border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.08)] p-2.5 text-[#f6c453]"><ClipboardCheck size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">A case playbook cannot become execution authority or bypass the governed response lifecycle.</p></section>
          <section className="soc-card p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Automation scope</p><p className="mt-3 text-xl font-semibold text-slate-100">Non-executing</p></div><div className="rounded-xl border border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.08)] p-2.5 text-[#69a7ff]"><Bot size={19} /></div></div><p className="mt-4 text-xs leading-5 text-slate-500">AI assistance and investigation context remain advisory-only and do not perform response actions.</p></section>
        </div>

        {policyOpen && <section className="mt-4 soc-card border-[rgba(72,225,193,0.16)] p-4"><div className="flex items-start gap-3"><LockKeyhole size={18} className="mt-0.5 shrink-0 text-[#48e1c1]" /><div><p className="text-sm font-medium text-slate-200">Governed case contract</p><p className="mt-1 text-xs leading-5 text-slate-500">Any case integration must bind records to authenticated tenant-owned alerts, enforce analyst capabilities and tenant scope for every lookup and transition, minimize displayed evidence, retain auditable state transitions, and keep playbook runs approval-bound and non-executing until the separate governed response lifecycle creates an HMAC-signed audit. The legacy case API remains retired.
</p></div><button type="button" onClick={() => setPolicyOpen(false)} className="soc-focus ml-auto text-slate-500 hover:text-slate-200" aria-label="Close policy"><X size={16} /></button></div></section>}

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.45fr_0.9fr]">
          <section className="soc-card overflow-hidden"><div className="flex flex-col gap-3 border-b border-white/[0.07] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="soc-eyebrow">Investigation queue</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Tenant-scoped cases</h2></div><button type="button" disabled className="inline-flex items-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.02] px-3 py-2 text-xs font-medium text-slate-600"><Plus size={14} /> Create from alert</button></div><div className="p-5"><div className="overflow-hidden rounded-xl border border-white/[0.07] bg-black/10"><div className="grid grid-cols-[0.8fr_1.1fr_0.8fr_0.7fr] gap-3 border-b border-white/[0.07] px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.11em] text-slate-600"><span>Case</span><span>Evidence binding</span><span>Status</span><span>Updated</span></div><div className="flex min-h-64 flex-col items-center justify-center px-6 text-center"><FileSearch size={27} className="text-slate-600" /><h3 className="mt-3 text-sm font-medium text-slate-300">No governed cases are available in this view</h3><p className="mt-2 max-w-md text-xs leading-5 text-slate-500">The prior client could create and alter incident workflow state through a legacy surface. This workspace remains intentionally empty until protected case discovery is bound to the supported tenant and capability controls.</p></div></div></div></section>

          <aside className="soc-card p-5"><div className="flex items-start justify-between gap-3"><div><p className="soc-eyebrow">Lifecycle control</p><h2 className="mt-1 text-lg font-semibold text-slate-100">From alert to governed response</h2></div><Network size={19} className="text-slate-500" /></div><div className="mt-5 divide-y divide-white/[0.06]"><LifecycleRow icon={ShieldAlert} title="Alert-linked case" detail="A case originates from an authenticated tenant-owned alert, not arbitrary browser input." state="Required" tone="teal" /><LifecycleRow icon={UserCheck} title="Analyst triage" detail="Every lookup and state transition must enforce the analyst capability and tenant boundary." state="Required" tone="teal" /><LifecycleRow icon={ClipboardCheck} title="Playbook request" detail="A playbook request remains an auditable workflow state, not direct response execution." state="Approval" tone="amber" /><LifecycleRow icon={CheckCircle2} title="Verify & rollback" detail="The separate governed response lifecycle retains controlled execution, verification, and rollback." state="Required" tone="teal" /></div><div className="mt-4 rounded-xl border border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.06)] p-3"><div className="flex items-center gap-2 text-[#f6c453]"><ShieldCheck size={15} /><p className="text-xs font-semibold">No direct execution controls</p></div><p className="mt-2 text-xs leading-5 text-slate-500">This page does not assign cases, change status, trigger playbooks, or execute containment actions.</p></div></aside>
        </div>
      </div>
    </div>
  );
};

export default CaseManagementPage;
