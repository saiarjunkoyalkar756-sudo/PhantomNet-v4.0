import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import MarketplaceGrid from '@/features/marketplace/components/MarketplaceGrid';

const MotionDiv = motion.div;

const Marketplace = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="PLUGIN & AI MARKETPLACE"
      subtitle="Fixture extension catalogues and simulated enablement controls are retired pending a governed extension lifecycle."
    />
    <div className="flex-1 min-h-0">
      <MarketplaceGrid />
    </div>
  </MotionDiv>
);

export default Marketplace;
