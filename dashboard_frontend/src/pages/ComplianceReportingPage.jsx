import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const ComplianceReportingPage = () => (
  <MotionDiv
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    className="p-6 space-y-6"
  >
    <PageHeader
      title="COMPLIANCE & SOC 2"
      subtitle="Legacy report generation, audit scoring, findings, and PDF artifact controls are retired pending governed evidence reporting."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Compliance Evidence Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard cannot generate, list, inspect, score, or download compliance reports. The legacy reporting flow was retired because its fixture artifacts and generated output did not establish tenant-scoped evidence provenance, report authorization, control-evaluation completeness, retention, or independently validated compliance semantics.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future reporting workflow must use tenant-scoped evidence, policy-controlled report generation, durable audit records, authorized artifact access, retention controls, and independently validated control mappings before it is exposed as an operational capability.
      </p>
    </section>
  </MotionDiv>
);

export default ComplianceReportingPage;
