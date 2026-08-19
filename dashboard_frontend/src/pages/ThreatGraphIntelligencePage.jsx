import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { GitGraph } from 'lucide-react';
import GraphCanvas from '@/features/threat-graph/components/GraphCanvas';

const MotionDiv = motion.div;

const ThreatGraphIntelligencePage = () => {
  return (
    <MotionDiv
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader
        title="THREAT GRAPH & INTELLIGENCE"
        subtitle="Visualize relationships between threats, attackers, and assets."
      />
      {/* Content for Threat Graph & Intelligence Page */}
      <div className="flex-1 min-h-0">
        <GraphCanvas />
      </div>
    </MotionDiv>
  );
};

export default ThreatGraphIntelligencePage;
