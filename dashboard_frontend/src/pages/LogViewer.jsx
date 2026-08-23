import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const LogViewer = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="STRUCTURED LOG VIEWER"
      subtitle="Fixture log streaming, local formatting, export, and inert search controls are retired pending governed log-evidence integration."
    />

    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Log-Evidence Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not stream, search, format, copy, export, or clear security logs. The prior client replayed fixture entries on a timer, including fabricated authentication, endpoint, database, payload, quarantine, and configuration events that could be mistaken for live tenant evidence.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future log view must use a protected tenant-scoped analyst workflow with authorization-checked, provenance-linked, minimized results; constrain queries and exports; redact or gate sensitive fields; retain deterministic auditability; and distinguish observed raw telemetry from verified analytical findings. It must not imply live ingestion, log completeness, detection efficacy, automatic containment, or response execution.
      </p>
    </section>
  </MotionDiv>
);

export default LogViewer;
