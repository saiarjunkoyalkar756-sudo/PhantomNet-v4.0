import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { NavLink } from 'react-router-dom';
import {
  Shield,
  LayoutGrid,
  Activity,
  GitGraph,
  Globe,
  Puzzle,
  BookCopy,
  Bot,
  Settings,
  ChevronsLeft,
  ChevronsRight,
  Fingerprint,
  Users,
  HardDriveDownload,
  Terminal,
  MessageSquare,
  Target
} from 'lucide-react';
import { cn } from '@/lib/utils';

const NavItem = ({ icon: Icon, text, to, expanded }) => {
    return (
        <motion.li whileHover={{ scale: expanded ? 1.02 : 1, x: expanded ? 5 : 0 }}>
            <NavLink
                to={to}
                className={({ isActive }) =>
                    cn(`
                        relative flex items-center py-3 px-4 my-1
                        font-medium rounded-md cursor-pointer
                        transition-colors group
                        font-mono text-sm
                        whitespace-nowrap
                        ${isActive
                            ? "bg-gradient-to-tr from-primary to-primary/50 text-primary-foreground shadow-lg"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        }
                    `)
                }
            >
                <Icon size={20} className="shrink-0" />
                <motion.span
                    initial={false}
                    animate={{ width: expanded ? "auto" : 0, opacity: expanded ? 1 : 0, marginLeft: expanded ? '0.75rem' : 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                >
                    {text}
                </motion.span>
            </NavLink>
             {!expanded && (
                <div
                    className={`
                        absolute left-full rounded-md px-3 py-2 ml-6
                        bg-card text-card-foreground text-sm
                        invisible opacity-0 -translate-x-3 transition-all
                        group-hover:visible group-hover:opacity-100 group-hover:translate-x-0
                        border shadow-md z-20
                    `}
                >
                    {text}
                </div>
            )}
        </motion.li>
    );
};


const Sidebar = () => {
    const [expanded, setExpanded] = useState(true);

    const navItems = [
        { icon: LayoutGrid, text: "Dashboard", to: "/dashboard" },
        { icon: Terminal, text: "Event Stream", to: "/events" },
        { icon: Users, text: "Agents", to: "/agents" },
        { icon: GitGraph, text: "Threat Graph", to: "/threat-graph" },
        { icon: Globe, text: "Threat Intel", to: "/intel" },
        { icon: MessageSquare, text: "AI Console", to: "/ai-console" },
        { icon: HardDriveDownload, text: "Marketplace", to: "/marketplace" },
        { icon: BookCopy, text: "Log Viewer", to: "/logs" },
        { icon: Target, text: "Red Team", to: "/red-team" },
    ];

    return (
        <motion.aside
            initial={false}
            animate={{ width: expanded ? "280px" : "80px" }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="h-screen p-4 flex flex-col bg-card border-r shadow-lg relative z-20"
        >
            <div className="flex items-center justify-between pb-4 border-b mb-4">
                <motion.div
                    animate={{ opacity: expanded ? 1 : 0, width: expanded ? "auto" : 0 }}
                    className="flex items-center gap-2 overflow-hidden"
                >
                    <Fingerprint size={28} className="text-primary shrink-0" />
                    <span className="font-bold text-xl text-primary whitespace-nowrap">PhantomNet</span>
                </motion.div>
                <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setExpanded(curr => !curr)}
                    className="p-2 rounded-full text-muted-foreground hover:bg-accent"
                >
                    {expanded ? <ChevronsLeft size={20} /> : <ChevronsRight size={20} />}
                </motion.button>
            </div>

            <ul className="flex-1">
                {navItems.map((item) => (
                    <NavItem key={item.to} {...item} expanded={expanded} />
                ))}
            </ul>

            <div className="border-t pt-4 mt-4">
                <NavItem icon={Settings} text="Settings" to="/settings" expanded={expanded} />
            </div>
        </motion.aside>
    );
};

export default Sidebar;