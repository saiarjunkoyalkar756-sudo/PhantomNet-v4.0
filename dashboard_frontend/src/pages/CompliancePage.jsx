import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const CompliancePage = () => (
  <div className="h-full flex flex-col">
    <PageHeader
      title="GOVERNANCE, RISK & COMPLIANCE"
      subtitle="Governed compliance-evidence integration is pending."
    />
    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Compliance-Evidence Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not run compliance audits, calculate framework scores or trends, present audit status, identify findings, generate remediation plans, provide AI recommendations, or create downloadable compliance reports. The prior screen combined fixture posture data, simulated audit progress, unsupported API fallback, and unverified security and regulatory claims.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future compliance workflow must use authorized tenant-scoped evidence, validated control mappings, reproducible assessment methods, source-linked findings, appropriately authorized report generation, and auditable review. Recommendations must remain advisory; any remediation requires separately governed human approval, verification, and rollback.
      </p>
    </section>
  </div>
);

export default CompliancePage;
