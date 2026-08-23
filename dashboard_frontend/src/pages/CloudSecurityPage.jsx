import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const CloudSecurityPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="CLOUD SECURITY"
      subtitle="Caller-supplied cloud credential checks and fixture posture findings are retired pending governed cloud integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Cloud Security Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard cannot accept cloud credentials, query cloud resources, enumerate buckets, detect IAM abuse, assess cloud misconfigurations, or present cloud-security findings. The legacy flow was retired because it accepted caller-supplied credentials and did not establish tenant-scoped authorization, provider controls, durable audit evidence, validated scope, or result provenance.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future cloud integration must use authorized credentials held outside the client, tenant-scoped provider authorization, policy-bound scope, auditable read-only collection, rate-limit controls, validated finding provenance, and approved change control for remediation before it is exposed as an operational capability.
      </p>
    </section>
  </MotionDiv>
);

export default CloudSecurityPage;
