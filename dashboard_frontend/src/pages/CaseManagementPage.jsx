import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const CaseManagementPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="INCIDENT CASE MANAGEMENT"
      subtitle="Direct legacy case CRUD, assignment, note, timeline, and playbook controls are retired pending governed case-lifecycle integration."
    />

    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Case-Lifecycle Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not create, list, inspect, assign, update, annotate, or close cases, and it does not expose playbook status or execute a playbook. The previous client called a legacy case surface and could create or change incident workflow state without the supported tenant and capability boundary.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        The separately protected governed case lifecycle remains the supported control plane. Any future dashboard integration must bind cases to authenticated tenant-owned alerts, enforce analyst capabilities and tenant scope for every lookup and transition, minimize displayed evidence, retain auditable state transitions, and keep playbook runs approval-bound and non-executing until a separately governed response lifecycle performs request, human approval, HMAC-signed audit, controlled execution, verification, and rollback.
      </p>
    </section>
  </MotionDiv>
);

export default CaseManagementPage;
