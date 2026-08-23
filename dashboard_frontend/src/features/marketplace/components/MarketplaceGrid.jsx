import { motion } from 'framer-motion';
import React from 'react';

const MotionDiv = motion.div;

const MarketplaceGrid = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6"
  >
    <h2 className="text-lg font-semibold text-primary">Governed Extension Lifecycle Pending</h2>
    <p className="mt-3 text-sm text-text-secondary leading-6">
      PhantomNet does not currently browse, install, configure, sign, enable, disable, or execute marketplace extensions through this dashboard. Fixture XDR, honeypot, AI, and blockchain plugin records and simulated signature and enablement state have been removed.
    </p>
    <p className="mt-3 text-sm text-text-secondary leading-6">
      Any future extension lifecycle must use trusted provenance, tenant-scoped configuration, reviewable permissions, approval-bound activation, durable audit evidence, rollback, and validated runtime isolation before it is exposed as an operational control.
    </p>
  </MotionDiv>
);

export default MarketplaceGrid;
