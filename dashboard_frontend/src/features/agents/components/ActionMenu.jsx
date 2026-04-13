import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';

const ActionMenu = ({ agentId, onApprove, onRevoke, onQuarantine, onViewDetails }) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4 text-text-secondary" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-panel-solid border-border text-text-primary">
        <DropdownMenuItem onClick={() => onViewDetails(agentId)} className="hover:bg-accent/20 cursor-pointer">
          View Details
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-border" />
        <DropdownMenuItem onClick={() => onApprove(agentId)} className="hover:bg-primary/20 text-primary cursor-pointer">
          Approve
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onRevoke(agentId)} className="hover:bg-destructive/20 text-destructive cursor-pointer">
          Revoke
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onQuarantine(agentId)} className="hover:bg-secondary/20 text-secondary cursor-pointer">
          Quarantine
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ActionMenu;
