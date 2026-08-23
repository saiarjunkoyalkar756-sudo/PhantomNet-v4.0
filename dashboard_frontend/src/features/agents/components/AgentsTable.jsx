import { motion } from 'framer-motion';
import React from 'react';

const MotionDiv = motion.div;

const AgentsTable = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6 font-mono"
  >
    <h2 className="text-lg font-semibold text-primary">Governed Endpoint Integration Pending</h2>
    <p className="mt-3 text-sm text-text-secondary leading-6">
      PhantomNet does not currently expose a tenant-scoped agent enrollment, inventory, lifecycle, or direct-command control plane through this dashboard. Legacy fixture fleet data and simulated approval, revocation, quarantine, certificate, and heartbeat controls have been removed.
    </p>
    <p className="mt-3 text-sm text-text-secondary leading-6">
      Endpoint actions must remain request-bound, human-approved, auditable, verified, and rollback-capable before this view can display operational controls.
    </p>
  </MotionDiv>
);

export default AgentsTable;
