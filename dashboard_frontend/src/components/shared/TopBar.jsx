import React from 'react';
import { motion } from 'framer-motion';
import { Search, Bell, User, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { ModeToggle } from './ThemeToggler';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import useAuthStore from '@/store/authStore';

const TopBar = () => {
  const { user, logout } = useAuthStore();

  return (
    <motion.header
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex-shrink-0 flex items-center justify-between p-4 bg-card/80 backdrop-blur-md border-b border-border shadow-sm"
    >
      {/* Search Bar */}
      <div className="relative w-full max-w-sm mr-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
        <input
          type="text"
          placeholder="Search PhantomNet..."
          className="w-full pl-10 pr-4 py-2 rounded-lg bg-background border border-input focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-all duration-300 text-foreground placeholder-muted-foreground"
        />
      </div>

      {/* Quick Actions & User Menu */}
      <div className="flex items-center space-x-4">
        <ModeToggle />
        <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-primary transition-colors">
            <Bell size={20} />
            <span className="absolute top-2 right-2 block h-2 w-2 rounded-full bg-destructive animate-pulse" />
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <motion.div
              className="flex items-center space-x-3 cursor-pointer group"
              whileHover={{ scale: 1.02 }}
            >
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-primary-foreground">
                    <User size={24} />
                </div>
                <div className="hidden md:block">
                    <p className="text-sm font-semibold text-foreground">{user?.email}</p>
                    <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
                </div>
            </motion.div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </motion.header>
  );
};

export default TopBar;

