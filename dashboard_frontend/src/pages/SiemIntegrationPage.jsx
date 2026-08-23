import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const SiemIntegrationPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="SIEM INTEGRATION"
      subtitle="Legacy SIEM connection configuration and event-forwarding controls are retired pending a governed telemetry integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed SIEM Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard cannot create, list, configure, or expose SIEM connections, and it cannot submit test events to external platforms. The legacy integration surface was retired because it did not establish tenant-scoped configuration custody, provider authorization, durable audit evidence, or validated delivery semantics.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future SIEM integration must use authorized provider credentials held outside the client, tenant-scoped configuration, policy-bound event routing, auditable delivery records, and independently validated provider behavior before it is exposed as an operational control.
      </p>
    </section>
  </MotionDiv>
);

export default SiemIntegrationPage;
