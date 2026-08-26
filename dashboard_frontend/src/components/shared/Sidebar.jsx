import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity, Bot, Boxes, ChevronLeft, ChevronRight, FileSearch, Fingerprint,
  GitBranch, LayoutDashboard, RadioTower, Settings, ShieldCheck, UsersRound,
} from 'lucide-react';

const sections = [
  { label: 'Operations', items: [
    { icon: LayoutDashboard, label: 'Command center', to: '/dashboard' },
    { icon: Activity, label: 'Event stream', to: '/events' },
    { icon: FileSearch, label: 'Case management', to: '/case-management' },
    { icon: RadioTower, label: 'Threat hunting', to: '/threat-hunting' },
  ] },
  { label: 'Response', items: [
    { icon: ShieldCheck, label: 'Governed response', to: '/soar' },
    { icon: UsersRound, label: 'Agents', to: '/agents' },
    { icon: GitBranch, label: 'Threat graph', to: '/threat-graph' },
  ] },
  { label: 'Platform', items: [
    { icon: Boxes, label: 'SIEM integration', to: '/siem-integration' },
    { icon: Bot, label: 'AI decision log', to: '/ai-decision-log' },
    { icon: Settings, label: 'Settings', to: '/settings' },
  ] },
];

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <aside className={`relative z-30 hidden h-screen shrink-0 flex-col border-r border-white/[0.08] bg-[#09111c] text-slate-300 transition-[width] duration-200 md:flex ${collapsed ? 'w-[76px]' : 'w-[252px]'}`}>
      <div className="flex h-[76px] items-center border-b border-white/[0.08] px-4">
        <div className="flex min-w-0 flex-1 items-center gap-3 overflow-hidden"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-[rgba(72,225,193,0.2)] bg-[rgba(72,225,193,0.08)] text-[#48e1c1]"><Fingerprint size={19} /></div>{!collapsed && <div className="min-w-0"><p className="truncate text-sm font-semibold tracking-tight text-slate-100">PhantomNet</p><p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">SOC console</p></div>}</div>
        <button type="button" onClick={() => setCollapsed((current) => !current)} className="soc-focus grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-500 transition hover:bg-white/[0.06] hover:text-slate-200" aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}>{collapsed ? <ChevronRight size={17} /> : <ChevronLeft size={17} />}</button>
      </div>
      <nav className="custom-scrollbar flex-1 overflow-y-auto px-3 py-5" aria-label="Primary">
        {sections.map((section) => <div key={section.label} className="mb-6">{!collapsed && <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-600">{section.label}</p>}<div className="space-y-1">{section.items.map((item) => { const Icon = item.icon; return <NavLink key={item.to} to={item.to} title={collapsed ? item.label : undefined} className={({ isActive }) => `soc-focus group flex items-center gap-3 rounded-lg px-2.5 py-2.5 text-sm transition ${isActive ? 'bg-[rgba(72,225,193,0.1)] text-[#85f1d8]' : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'}`}><Icon size={17} className="shrink-0" strokeWidth={1.8} />{!collapsed && <span className="truncate">{item.label}</span>}</NavLink>; })}</div></div>)}
      </nav>
      <div className="m-3 rounded-xl border border-white/[0.08] bg-white/[0.025] p-3">{!collapsed ? <><div className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#48e1c1]" /><p className="text-xs font-medium text-slate-300">Evidence-first mode</p></div><p className="mt-2 text-[11px] leading-4 text-slate-500">Response remains approval-bound and deployment-gated.</p></> : <span className="mx-auto block h-2 w-2 rounded-full bg-[#48e1c1]" />}</div>
    </aside>
  );
};

export default Sidebar;
