import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const SOARPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="h-full flex flex-col space-y-6"
  >
    <PageHeader
      title="SOAR & GOVERNED CONTAINMENT"
      subtitle="Fixture playbooks, simulated approvals, manual mitigation, execution history, and containment claims are retired pending a dashboard integration with the governed containment control plane."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Containment Dashboard Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard cannot create or modify playbooks, approve or deny response actions, trigger mitigation, display execution status, manage firewall blocks, or assert automatic containment, blockchain audit, or remediation outcomes. The legacy SOAR view relied on fixture state and local simulation that bypassed the required approval, audit, verification, and rollback lifecycle.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        The supported governed containment control plane remains separately protected. Any future dashboard integration must remain tenant-scoped and capability-protected, issue a request before human decision, retain HMAC-signed audit evidence, use controlled adapters, verify execution, and support rollback. High-impact containment must never become automatic through the client.
      </p>
    </section>
  </MotionDiv>
);

export default SOARPage;
