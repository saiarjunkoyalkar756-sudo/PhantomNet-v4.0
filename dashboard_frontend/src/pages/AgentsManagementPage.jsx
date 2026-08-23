import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import AgentsTable from '@/features/agents/components/AgentsTable';

const MotionDiv = motion.div;

const AgentsManagementPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="AGENT MANAGEMENT"
      subtitle="Legacy agent enrollment and lifecycle controls are retired pending a governed, tenant-scoped endpoint control plane."
    />

    <div className="flex-1 min-h-0">
      <AgentsTable />
    </div>
  </MotionDiv>
);

export default AgentsManagementPage;
