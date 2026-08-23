import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const SandboxPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="MALWARE SANDBOX"
      subtitle="Legacy file-upload and sandbox-analysis controls are retired pending an isolated, governed analysis integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Malware Analysis Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard cannot upload suspicious files, execute them, or report behavioral, network, cryptographic, artifact, verdict, hash, or raw-analysis results. The legacy sandbox API was retired because it did not establish the required isolated execution, authorization, evidence, retention, and safe handling boundaries.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future analysis workflow must use authorized submission, isolated execution, tenant-scoped evidence handling, auditable lifecycle controls, and validated result provenance before it is presented as an operational capability.
      </p>
    </section>
  </MotionDiv>
);

export default SandboxPage;
