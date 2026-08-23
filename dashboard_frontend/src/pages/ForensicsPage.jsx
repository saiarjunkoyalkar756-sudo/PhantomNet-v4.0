import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const ForensicsPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="h-full flex flex-col space-y-6"
  >
    <PageHeader
      title="FORENSICS & EVIDENCE"
      subtitle="Fixture acquisition jobs, evidence artifacts, timelines, integrity claims, and export controls are retired pending governed forensics integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Forensics Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard cannot initiate forensic acquisition, inspect job status, display evidence artifacts, reconstruct attack timelines, assert custody integrity, acquire artifacts, or export forensic reports. The legacy view relied on fixture artifacts and simulated job/timeline state that could be mistaken for live investigation evidence.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future workflow must use authorized collection targets, tenant-scoped evidence, immutable custody records, controlled artifact access, validated timeline provenance, policy-bound task execution, human approval where required, retention controls, verification, and rollback before it is exposed as an operational capability.
      </p>
    </section>
  </MotionDiv>
);

export default ForensicsPage;
