import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const SelfHealingConsolePage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="SELF-HEALING CONSOLE"
      subtitle="Legacy autonomous endpoint status and remediation controls are retired pending a governed response integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Response Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not currently retrieve endpoint health, error, certificate, or self-healing status from the retired legacy agent API. It also cannot trigger repair, patch, recovery, safe-mode, or self-healing changes.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future endpoint response capability must be tenant-scoped, evidence-bound, human-approved for high-impact actions, auditable, verified, and rollback-capable before it is exposed as an operational control.
      </p>
    </section>
  </MotionDiv>
);

export default SelfHealingConsolePage;
