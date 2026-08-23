import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const AIDecisionLogPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="ADVISORY DECISION EVIDENCE"
      subtitle="Placeholder decision polling, raw details, confidence display, execution traces, and autonomous-action claims are retired pending governed advisory evidence-log integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Advisory Evidence-Log Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not present AI decisions, confidence values, execution traces, agent outcomes, or raw investigation details. The legacy view polled an unsupported endpoint and could imply autonomous action or verified model efficacy without source-linked, tenant-scoped evidence.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future advisory view must use tenant-scoped, provenance-linked observations; minimize displayed evidence; distinguish recommendations from deterministic findings; remain policy-gated and non-executing; and preserve approval-bound containment rather than implying autonomous remediation.
      </p>
    </section>
  </MotionDiv>
);

export default AIDecisionLogPage;
