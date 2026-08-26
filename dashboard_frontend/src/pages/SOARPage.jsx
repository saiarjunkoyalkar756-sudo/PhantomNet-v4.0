import { createElement, useEffect, useMemo, useState } from 'react';
import {
  BadgeCheck, Bot, CheckCircle2, ChevronDown, CircleAlert, ClipboardCheck,
  FileCheck2, Fingerprint, LockKeyhole, Play, RefreshCw, RotateCcw,
  ShieldCheck, ShieldOff, Sparkles, UserCheck, XCircle,
} from 'lucide-react';

import {
  createContainmentRequest,
  decideContainmentRequest,
  evaluateDefenseDetection,
  executeContainmentRequest,
  fetchContainmentPreflight,
  fetchContainmentRequests,
  fetchDefenseDecisions,
  fetchDefensePolicies,
  rollbackContainmentRequest,
  verifyContainmentAudit,
} from '@/services/governedResponse.service';

const MetricCard = ({ icon: Icon, label, value, detail, tone = 'blue' }) => {
  const tones = {
    blue: 'border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.08)] text-[#69a7ff]',
    teal: 'border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]',
    amber: 'border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.08)] text-[#f6c453]',
    rose: 'border-[rgba(242,109,120,0.16)] bg-[rgba(242,109,120,0.08)] text-[#f26d78]',
  };
  return <section className="soc-card p-5"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">{label}</p><p className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-slate-100">{value ?? '—'}</p></div><div className={`rounded-xl border p-2.5 ${tones[tone]}`}>{createElement(Icon, { size: 19 })}</div></div><p className="mt-4 text-xs leading-5 text-slate-500">{detail}</p></section>;
};

const StatusPill = ({ value }) => {
  const normalized = String(value || 'unknown').toLowerCase();
  const tone = normalized.includes('verified') || normalized.includes('approved') || normalized.includes('recorded') ? 'bg-[rgba(72,225,193,0.1)] text-[#48e1c1]' : normalized.includes('failed') || normalized.includes('rejected') || normalized.includes('refused') ? 'bg-[rgba(242,109,120,0.1)] text-[#f26d78]' : normalized.includes('proposed') || normalized.includes('pending') || normalized.includes('requested') ? 'bg-[rgba(246,196,83,0.1)] text-[#f6c453]' : 'bg-white/[0.06] text-slate-400';
  return <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.09em] ${tone}`}>{String(value || 'unknown').replaceAll('_', ' ')}</span>;
};

const LifecycleStep = ({ icon: Icon, title, detail, state, tone = 'slate' }) => {
  const tones = { slate: 'border-white/[0.08] bg-white/[0.03] text-slate-400', teal: 'border-[rgba(72,225,193,0.18)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]', amber: 'border-[rgba(246,196,83,0.18)] bg-[rgba(246,196,83,0.08)] text-[#f6c453]' };
  return <div className="flex gap-3 py-3"><div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${tones[tone]}`}>{createElement(Icon, { size: 15 })}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-3"><p className="text-sm font-medium text-slate-200">{title}</p><StatusPill value={state} /></div><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div></div>;
};

const makeIdempotencyKey = () => window.crypto.randomUUID();

const SOARPage = () => {
  const [requests, setRequests] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [selectedRequestId, setSelectedRequestId] = useState('');
  const [preflight, setPreflight] = useState(null);
  const [auditVerification, setAuditVerification] = useState(null);
  const [action, setAction] = useState('isolate_endpoint');
  const [target, setTarget] = useState('');
  const [assetId, setAssetId] = useState('');
  const [playbookId, setPlaybookId] = useState('');
  const [wazuhAgentId, setWazuhAgentId] = useState('');
  const [approvalReason, setApprovalReason] = useState('');
  const [detectionId, setDetectionId] = useState('');
  const [triageResult, setTriageResult] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPreflightLoading, setIsPreflightLoading] = useState(false);
  const [isTriageLoading, setIsTriageLoading] = useState(false);

  const selectedRequest = useMemo(() => requests.find((request) => request.request_id === selectedRequestId) || null, [requests, selectedRequestId]);
  const requestedCount = requests.filter((request) => request.status === 'requested').length;
  const approvedCount = requests.filter((request) => request.status === 'approved').length;

  const loadPreflight = async (requestId) => {
    if (!requestId) {
      setPreflight(null);
      return;
    }
    setIsPreflightLoading(true);
    try {
      setPreflight(await fetchContainmentPreflight(requestId));
    } catch (requestError) {
      setPreflight(null);
      setError(requestError.message || 'Containment readiness is currently unavailable.');
    } finally {
      setIsPreflightLoading(false);
    }
  };

  const loadWorkspace = async ({ refresh = false } = {}) => {
    if (refresh) setIsRefreshing(true);
    try {
      const [requestData, policyData, decisionData] = await Promise.all([
        fetchContainmentRequests(),
        fetchDefensePolicies(),
        fetchDefenseDecisions(),
      ]);
      setRequests(requestData);
      setPolicies(policyData);
      setDecisions(decisionData);
      setSelectedRequestId((current) => current && requestData.some((request) => request.request_id === current) ? current : (requestData[0]?.request_id || ''));
      setError('');
    } catch (requestError) {
      setError(requestError.message || 'The governed response control plane is currently unavailable.');
    } finally {
      if (refresh) setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    loadPreflight(selectedRequestId);
  }, [selectedRequestId]);

  const createRequest = async () => {
    if (!target.trim()) {
      setError('Provide a scoped target before creating a containment request.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const parameters = wazuhAgentId.trim() ? { wazuh_agent_id: wazuhAgentId.trim() } : {};
      const response = await createContainmentRequest({
        action,
        target: target.trim(),
        asset_id: assetId.trim() || null,
        playbook_id: playbookId.trim() || null,
        idempotency_key: makeIdempotencyKey(),
        parameters,
      });
      setTarget('');
      setAssetId('');
      setPlaybookId('');
      setWazuhAgentId('');
      await loadWorkspace();
      setSelectedRequestId(response.request.request_id);
    } catch (requestError) {
      setError(requestError.message || 'The containment request could not be created.');
    } finally {
      setIsLoading(false);
    }
  };

  const decideRequest = async (decision) => {
    if (!selectedRequestId || approvalReason.trim().length < 3) {
      setError('Provide a human decision reason of at least three characters.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await decideContainmentRequest(selectedRequestId, { decision, reason: approvalReason.trim() });
      setApprovalReason('');
      await loadWorkspace();
      await loadPreflight(selectedRequestId);
    } catch (requestError) {
      setError(requestError.message || 'The human decision could not be recorded.');
    } finally {
      setIsLoading(false);
    }
  };

  const executeRequest = async () => {
    if (!selectedRequestId) return;
    setIsLoading(true);
    setError('');
    try {
      await executeContainmentRequest(selectedRequestId);
      await loadWorkspace();
      await loadPreflight(selectedRequestId);
    } catch (requestError) {
      setError(requestError.message || 'Execution was refused by the governed response control plane.');
    } finally {
      setIsLoading(false);
    }
  };

  const rollbackRequest = async () => {
    if (!selectedRequestId) return;
    setIsLoading(true);
    setError('');
    try {
      await rollbackContainmentRequest(selectedRequestId);
      await loadWorkspace();
      await loadPreflight(selectedRequestId);
    } catch (requestError) {
      setError(requestError.message || 'Rollback was refused by the governed response control plane.');
    } finally {
      setIsLoading(false);
    }
  };

  const verifyAudit = async () => {
    setIsLoading(true);
    setError('');
    try {
      setAuditVerification(await verifyContainmentAudit());
    } catch (requestError) {
      setAuditVerification(null);
      setError(requestError.message || 'Signed audit verification is currently unavailable.');
    } finally {
      setIsLoading(false);
    }
  };

  const evaluateTriage = async () => {
    if (!detectionId.trim()) {
      setError('Provide a tenant-owned detection identifier for advisory evaluation.');
      return;
    }
    setIsTriageLoading(true);
    setError('');
    try {
      setTriageResult(await evaluateDefenseDetection(detectionId.trim()));
      setDetectionId('');
      setDecisions(await fetchDefenseDecisions());
    } catch (requestError) {
      setError(requestError.message || 'The advisory triage evaluation could not be completed.');
    } finally {
      setIsTriageLoading(false);
    }
  };

  return (
    <div className="soc-page soc-grid">
      <div className="mx-auto max-w-[1600px]">
        <header className="mb-7 flex flex-col justify-between gap-5 xl:flex-row xl:items-end"><div><p className="soc-eyebrow">GOVERNED RESPONSE · Human decision required</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-100 sm:text-4xl">Incident response control plane</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Create a scoped request, obtain a recorded human decision, evaluate side-effect-free readiness, then use a controlled adapter with verification and rollback. A playbook reference is request metadata, not an execution shortcut.</p></div><div className="flex flex-wrap items-center gap-2"><span className="inline-flex items-center gap-2 rounded-full border border-white/[0.09] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400" aria-label="Governed Containment Dashboard Integration Pending"><span className="h-1.5 w-1.5 rounded-full bg-slate-500" />Control plane evidence</span><button type="button" onClick={() => loadWorkspace({ refresh: true })} disabled={isRefreshing} className="soc-focus inline-flex items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-50"><RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} /> Refresh</button></div></header>

        {error && <div className="mb-5 flex items-start gap-3 rounded-xl border border-[rgba(246,196,83,0.22)] bg-[rgba(246,196,83,0.08)] px-4 py-3 text-sm text-[#f6c453]" role="status"><CircleAlert size={18} className="mt-0.5 shrink-0" /><p>{error}</p></div>}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"><MetricCard icon={ClipboardCheck} label="Requests awaiting decision" value={requests.length ? requestedCount : null} detail={requests.length ? 'Tenant-scoped response requests with a requested state.' : 'Awaiting authorized request records.'} tone="amber" /><MetricCard icon={UserCheck} label="Approved requests" value={requests.length ? approvedCount : null} detail={requests.length ? 'Approval state is supplied by the governed control plane.' : 'No approval volume is inferred client-side.'} tone="teal" /><MetricCard icon={Bot} label="Advisory policies" value={policies.length || null} detail={policies.length ? 'Durable triage policy records returned for this tenant.' : 'No policy count is shown without returned evidence.'} tone="blue" /><MetricCard icon={FileCheck2} label="Recorded triage decisions" value={decisions.length || null} detail={decisions.length ? 'Immutable, tenant-scoped triage records from the response plane.' : 'No decision count is shown without returned evidence.'} tone="rose" /></div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]"><section className="soc-card overflow-hidden"><div className="border-b border-white/[0.07] px-5 py-4"><p className="soc-eyebrow">Containment request</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Create an approval-bound response request</h2><p className="mt-2 text-xs leading-5 text-slate-500">The server requires `response:request`, HMAC-signed audit readiness, and a unique idempotency key. This form cannot mark a request approved or send an adapter command.</p></div><div className="p-5"><div className="grid gap-3 md:grid-cols-2"><label className="block"><span className="text-xs font-medium text-slate-300">Canonical action</span><select value={action} onChange={(event) => setAction(event.target.value)} className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200"><option value="isolate_endpoint">Isolate endpoint</option><option value="release_endpoint">Release endpoint</option><option value="block_indicator">Block indicator</option></select></label><label className="block"><span className="text-xs font-medium text-slate-300">Scoped target</span><input value={target} onChange={(event) => setTarget(event.target.value)} placeholder="asset or indicator identifier" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200 placeholder:text-slate-600" /></label><label className="block"><span className="text-xs font-medium text-slate-300">Asset reference <span className="text-slate-600">optional</span></span><input value={assetId} onChange={(event) => setAssetId(event.target.value)} placeholder="tenant asset identifier" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200 placeholder:text-slate-600" /></label><label className="block"><span className="text-xs font-medium text-slate-300">Playbook reference <span className="text-slate-600">optional</span></span><input value={playbookId} onChange={(event) => setPlaybookId(event.target.value)} placeholder="governed playbook reference" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200 placeholder:text-slate-600" /></label></div><label className="mt-3 block"><span className="text-xs font-medium text-slate-300">Wazuh agent reference <span className="text-slate-600">optional, adapter routing only</span></span><input value={wazuhAgentId} onChange={(event) => setWazuhAgentId(event.target.value)} placeholder="wazuh agent id" className="soc-focus mt-2 h-10 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 text-sm text-slate-200 placeholder:text-slate-600" /></label><div className="mt-4 flex flex-wrap items-center gap-3"><button type="button" onClick={createRequest} disabled={isLoading} className="soc-focus inline-flex h-10 items-center gap-2 rounded-lg bg-[#69a7ff] px-4 text-sm font-semibold text-[#06121c] transition hover:bg-[#8bbcff] disabled:cursor-not-allowed disabled:opacity-50"><ClipboardCheck size={15} />{isLoading ? 'Recording request…' : 'Create governed request'}</button><span className="text-xs text-slate-500">No adapter is called during request creation.</span></div></div></section>

          <aside className="soc-card p-5"><p className="soc-eyebrow">Control sequence</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Non-bypassable lifecycle</h2><div className="mt-4 divide-y divide-white/[0.06]"><LifecycleStep icon={ClipboardCheck} title="1. Request" detail="A tenant-scoped request is persisted with an HMAC-auditable record." state="required" tone="teal" /><LifecycleStep icon={UserCheck} title="2. Human decision" detail="A separate approver must record a reason before readiness can be eligible." state="required" tone="teal" /><LifecycleStep icon={ShieldCheck} title="3. Preflight" detail="Readiness is side-effect-free and checks audit, adapter, and rollback conditions." state="required" tone="amber" /><LifecycleStep icon={BadgeCheck} title="4. Controlled execution" detail="Only an approved eligible request may contact its selected adapter and record verification." state="gated" tone="amber" /><LifecycleStep icon={RotateCcw} title="5. Verify & rollback" detail="Rollback remains available only when verified execution evidence permits it." state="required" tone="teal" /></div><div className="mt-3 rounded-xl border border-[rgba(246,196,83,0.16)] bg-[rgba(246,196,83,0.06)] p-3 text-xs leading-5 text-slate-400">HMAC-signed audit evidence is required for high-impact response. High-impact containment must never become automatic through the client.</div></aside></div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]"><section className="soc-card overflow-hidden"><div className="flex flex-col gap-3 border-b border-white/[0.07] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="soc-eyebrow">Request ledger</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Tenant-scoped containment requests</h2></div><span className="text-xs text-slate-500">Select a request to inspect readiness.</span></div><div className="max-h-[28rem] overflow-y-auto divide-y divide-white/[0.06]">{requests.map((request) => <button key={request.request_id} type="button" onClick={() => setSelectedRequestId(request.request_id)} className={`soc-focus flex w-full items-center gap-3 px-5 py-4 text-left transition hover:bg-white/[0.02] ${request.request_id === selectedRequestId ? 'bg-[rgba(105,167,255,0.06)]' : ''}`}><div className={`h-2 w-2 shrink-0 rounded-full ${request.request_id === selectedRequestId ? 'bg-[#69a7ff]' : 'bg-slate-600'}`} /><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><p className="truncate text-sm font-medium text-slate-200">{request.action.replaceAll('_', ' ')} · {request.target}</p><StatusPill value={request.status} /></div><p className="mt-1 truncate font-mono text-xs text-slate-500">{request.request_id}</p></div><ChevronDown size={15} className={`shrink-0 text-slate-600 transition-transform ${request.request_id === selectedRequestId ? '-rotate-90' : 'rotate-90'}`} /></button>)}{!requests.length && <div className="flex min-h-60 flex-col items-center justify-center px-6 text-center"><ShieldOff size={26} className="text-slate-600" /><p className="mt-3 text-sm font-medium text-slate-300">No governed response requests are available</p><p className="mt-1 max-w-md text-xs leading-5 text-slate-500">This view does not use fixture playbooks, simulated approvals, or local execution history. Create a permitted request only when an authorized analyst workflow supplies a scoped target.</p></div>}</div></section>

          <aside className="soc-card p-5"><div className="flex items-start justify-between gap-3"><div><p className="soc-eyebrow">Readiness & human decision</p><h2 className="mt-1 text-lg font-semibold text-slate-100">{selectedRequest ? 'Selected request' : 'Select a request'}</h2></div>{isPreflightLoading ? <RefreshCw size={17} className="animate-spin text-slate-500" /> : <Fingerprint size={18} className="text-[#69a7ff]" />}</div>{selectedRequest ? <div className="mt-4"><div className="rounded-xl border border-white/[0.07] bg-black/10 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-mono text-xs text-slate-300">{selectedRequest.request_id}</p><StatusPill value={selectedRequest.status} /></div><p className="mt-2 text-sm text-slate-200">{selectedRequest.action.replaceAll('_', ' ')} · {selectedRequest.target}</p><p className="mt-1 text-xs text-slate-500">Playbook reference: {selectedRequest.playbook_id || 'not supplied'}</p></div><div className="mt-3 grid grid-cols-2 gap-2"><div className="rounded-lg border border-white/[0.07] bg-black/10 p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">Audit</p><p className="mt-1 text-sm text-slate-200">{preflight?.audit_ready ? 'Ready' : 'Not ready'}</p></div><div className="rounded-lg border border-white/[0.07] bg-black/10 p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">Adapter</p><p className="mt-1 truncate text-sm text-slate-200">{preflight?.adapter?.provider || 'Awaiting preflight'}</p></div></div><p className="mt-3 text-xs leading-5 text-slate-500">{preflight?.adapter?.detail || 'Preflight is read-only and never contacts an adapter.'}</p><div className="mt-3 rounded-xl border border-[rgba(105,167,255,0.15)] bg-[rgba(105,167,255,0.05)] p-3"><p className="text-xs font-medium text-slate-300">Execution blockers</p><p className="mt-1 text-xs leading-5 text-slate-500">{preflight?.execution_blockers?.length ? preflight.execution_blockers.join(' · ') : 'No preflight result has been returned.'}</p></div><label className="mt-3 block"><span className="text-xs font-medium text-slate-300">Human decision reason</span><textarea value={approvalReason} onChange={(event) => setApprovalReason(event.target.value)} placeholder="Record the approval or rejection rationale" className="soc-focus mt-2 min-h-20 w-full rounded-lg border border-white/[0.09] bg-black/10 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600" /></label><div className="mt-3 grid grid-cols-2 gap-2"><button type="button" onClick={() => decideRequest('approved')} disabled={isLoading || selectedRequest.status !== 'requested'} className="soc-focus inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[rgba(72,225,193,0.22)] bg-[rgba(72,225,193,0.08)] text-xs font-semibold text-[#48e1c1] transition hover:bg-[rgba(72,225,193,0.14)] disabled:cursor-not-allowed disabled:opacity-40"><CheckCircle2 size={14} />Record approval</button><button type="button" onClick={() => decideRequest('rejected')} disabled={isLoading || selectedRequest.status !== 'requested'} className="soc-focus inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[rgba(242,109,120,0.22)] bg-[rgba(242,109,120,0.08)] text-xs font-semibold text-[#f26d78] transition hover:bg-[rgba(242,109,120,0.14)] disabled:cursor-not-allowed disabled:opacity-40"><XCircle size={14} />Record rejection</button></div><div className="mt-2 grid grid-cols-2 gap-2"><button type="button" onClick={executeRequest} disabled={isLoading || !preflight?.eligible_to_execute} className="soc-focus inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[#f6c453] text-xs font-semibold text-[#221809] transition hover:bg-[#f8d074] disabled:cursor-not-allowed disabled:opacity-40"><Play size={14} />Execute approved</button><button type="button" onClick={rollbackRequest} disabled={isLoading || !preflight?.rollback_ready} className="soc-focus inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] text-xs font-semibold text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-40"><RotateCcw size={14} />Rollback verified</button></div></div> : <div className="flex min-h-72 flex-col items-center justify-center text-center"><LockKeyhole size={25} className="text-slate-600" /><p className="mt-3 text-sm font-medium text-slate-300">No response request selected</p><p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">Readiness, decision, execution, and rollback controls are unavailable until an authenticated tenant-scoped request has been selected.</p></div>}</aside></div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]"><section className="soc-card overflow-hidden"><div className="border-b border-white/[0.07] px-5 py-4"><p className="soc-eyebrow">Automated triage · advisory-only</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Evaluate evidence for human review</h2><p className="mt-2 text-xs leading-5 text-slate-500">The response plane evaluates only a persisted tenant-owned detection. It may record an immutable decision or approval-bound containment proposal; it never executes an adapter.</p></div><div className="p-5"><div className="flex flex-col gap-3 sm:flex-row"><input value={detectionId} onChange={(event) => setDetectionId(event.target.value)} placeholder="tenant detection identifier" className="soc-focus h-10 min-w-0 flex-1 rounded-lg border border-white/[0.09] bg-black/10 px-3 font-mono text-sm text-slate-200 placeholder:text-slate-600" /><button type="button" onClick={evaluateTriage} disabled={isTriageLoading} className="soc-focus inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[#48e1c1] px-4 text-sm font-semibold text-[#06121c] transition hover:bg-[#6ee9ce] disabled:cursor-not-allowed disabled:opacity-50"><Sparkles size={15} />{isTriageLoading ? 'Evaluating…' : 'Evaluate advisory triage'}</button></div>{triageResult ? <div className="mt-4 rounded-xl border border-[rgba(105,167,255,0.16)] bg-[rgba(105,167,255,0.05)] p-4"><div className="flex flex-wrap items-center justify-between gap-3"><p className="font-mono text-xs text-slate-300">Detection: {triageResult.detection_id}</p><StatusPill value={triageResult.automatic_enforcement ? 'unexpected enforcement' : 'no automatic enforcement'} /></div><div className="mt-3 space-y-2">{triageResult.decisions?.map((decision) => <div key={decision.decision_id} className="rounded-lg border border-white/[0.07] bg-black/10 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-medium text-slate-200">{decision.policy_name || decision.decision_mode || 'Advisory policy decision'}</p><StatusPill value={decision.outcome} /></div><p className="mt-1 text-xs leading-5 text-slate-500">{decision.reason || 'No additional decision rationale was returned.'}</p><p className="mt-2 text-xs text-slate-600">Human approval required: {decision.requires_human_approval ? 'yes' : 'not applicable'} · Response authority: none</p></div>)}{!triageResult.decisions?.length && <p className="text-xs leading-5 text-slate-500">The evaluation returned no advisory decision records.</p>}</div></div> : <div className="mt-4 rounded-xl border border-dashed border-white/[0.1] px-4 py-6 text-center text-xs leading-5 text-slate-500">No triage evaluation is selected. The client does not create confidence scores, evidence, or outcomes locally.</div>}</div></section>
          <aside className="soc-card p-5"><div className="flex items-start justify-between gap-3"><div><p className="soc-eyebrow">Audit & immutable decisions</p><h2 className="mt-1 text-lg font-semibold text-slate-100">Evidence record posture</h2></div><Fingerprint size={18} className="text-[#69a7ff]" /></div><button type="button" onClick={verifyAudit} disabled={isLoading} className="soc-focus mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.03] text-xs font-medium text-slate-300 transition hover:border-white/[0.18] hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-50"><Fingerprint size={14} />Verify signed audit chain</button>{auditVerification ? <div className="mt-3 rounded-xl border border-white/[0.07] bg-black/10 p-3"><div className="flex items-center justify-between gap-2"><p className="text-sm font-medium text-slate-200">Audit verification</p><StatusPill value={auditVerification.valid ? 'valid' : 'invalid'} /></div><p className="mt-2 text-xs leading-5 text-slate-500">{auditVerification.record_count} signed containment records checked for the authenticated tenant.</p></div> : <p className="mt-3 text-xs leading-5 text-slate-500">Verification is performed server-side with the configured HMAC signing key and never exposes key material to this client.</p>}<div className="mt-4 space-y-2">{decisions.slice(0, 4).map((decision) => <div key={decision.decision_id} className="rounded-xl border border-white/[0.07] bg-black/10 p-3"><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-medium text-slate-200">{decision.policy_name || decision.decision_mode || 'Triage decision'}</p><StatusPill value={decision.outcome} /></div><p className="mt-1 truncate font-mono text-xs text-slate-500">{decision.decision_id}</p></div>)}{!decisions.length && <div className="rounded-xl border border-dashed border-white/[0.1] px-4 py-5 text-center text-xs leading-5 text-slate-500">No advisory decision records are available from the protected response plane.</div>}</div></aside></div>
      </div>
    </div>
  );
};

export default SOARPage;
