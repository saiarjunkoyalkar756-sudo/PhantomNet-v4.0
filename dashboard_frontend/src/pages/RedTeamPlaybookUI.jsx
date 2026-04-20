import React, { useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Target, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import PlaybookList from '@/features/red-team/components/PlaybookList';

const RedTeamPlaybookUI = () => {
  const handleRunPlaybook = (id) => {
    alert(`Running playbook: ${id}`);
    // Simulate API call to run playbook
  };

  const handleViewReport = (id) => {
    alert(`Viewing report for playbook: ${id}`);
    // Navigate to report viewer or open a modal
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="RED TEAM PLAYBOOK"
        subtitle="Manage and execute attack simulations and security assessments."
        actions={
            <Button className="bg-destructive hover:bg-destructive/90 text-destructive-foreground">
                <Play className="w-4 h-4 mr-2" />RUN NEW SIMULATION
            </Button>
        }
      />
      {/* Content for Red Team Playbook UI */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
        <PlaybookList onRunPlaybook={handleRunPlaybook} onViewReport={handleViewReport} />
      </div>
    </motion.div>
  );
};

export default RedTeamPlaybookUI;
