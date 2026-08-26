import { useState } from 'react';
import { Bell, ChevronDown, Command, LogOut, Menu, Search, ShieldCheck, User } from 'lucide-react';
import { ModeToggle } from './ThemeToggler';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import useAuthStore from '@/store/authStore';

const TopBar = () => {
  const { user, logout } = useAuthStore();
  const [searchOpen, setSearchOpen] = useState(false);
  return (
    <header className="relative z-20 flex min-h-[76px] items-center justify-between gap-4 border-b border-white/[0.08] bg-[#09111c]/92 px-5 backdrop-blur-xl md:px-7">
      <div className="flex min-w-0 items-center gap-3"><button type="button" className="soc-focus grid h-9 w-9 place-items-center rounded-lg border border-white/[0.08] text-slate-400 md:hidden" aria-label="Open navigation"><Menu size={18} /></button><div className="hidden items-center gap-2 lg:flex"><span className="inline-flex h-6 items-center rounded-md border border-[rgba(72,225,193,0.16)] bg-[rgba(72,225,193,0.07)] px-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#48e1c1]"><ShieldCheck size={12} className="mr-1.5" />Evidence scope</span><span className="text-xs text-slate-500">Tenant-scoped analyst console</span></div></div>
      <div className="flex items-center gap-2 sm:gap-3"><div className={`hidden items-center rounded-lg border transition sm:flex ${searchOpen ? 'border-[rgba(72,225,193,0.35)] bg-white/[0.06]' : 'border-white/[0.08] bg-white/[0.025]'}`}><Search size={15} className="ml-3 text-slate-500" /><input onFocus={() => setSearchOpen(true)} onBlur={() => setSearchOpen(false)} aria-label="Search governed evidence" placeholder="Search evidence" className="h-9 w-36 bg-transparent px-2 text-xs text-slate-200 outline-none placeholder:text-slate-600 lg:w-52" /><span className="mr-2 inline-flex items-center gap-1 rounded border border-white/[0.08] px-1.5 py-0.5 text-[10px] text-slate-600"><Command size={10} />K</span></div><button type="button" className="soc-focus grid h-9 w-9 place-items-center rounded-lg border border-white/[0.08] bg-white/[0.025] text-slate-400 transition hover:bg-white/[0.06] hover:text-slate-200" aria-label="Notifications"><Bell size={17} /></button><ModeToggle />
        <DropdownMenu><DropdownMenuTrigger asChild><button type="button" className="soc-focus hidden items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.025] py-1.5 pl-1.5 pr-2 text-left transition hover:bg-white/[0.06] sm:flex"><span className="grid h-6 w-6 place-items-center rounded-md bg-[#203b52] text-[10px] font-semibold text-[#b7e5ff]">{user?.email?.slice(0, 2).toUpperCase() || 'AN'}</span><span className="hidden max-w-28 truncate text-xs font-medium text-slate-300 lg:inline">{user?.email || 'Analyst'}</span><ChevronDown size={14} className="text-slate-500" /></button></DropdownMenuTrigger><DropdownMenuContent align="end" className="w-52"><DropdownMenuItem><User className="mr-2 h-4 w-4" /><span>{user?.role || 'Analyst'}</span></DropdownMenuItem><DropdownMenuSeparator /><DropdownMenuItem onClick={logout}><LogOut className="mr-2 h-4 w-4" /><span>Log out</span></DropdownMenuItem></DropdownMenuContent></DropdownMenu>
      </div>
    </header>
  );
};

export default TopBar;
