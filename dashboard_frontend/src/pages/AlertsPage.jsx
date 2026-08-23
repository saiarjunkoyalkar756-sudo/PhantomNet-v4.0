import React from 'react';

const AlertsPage = () => (
  <div className="container mx-auto p-4">
    <section className="rounded-lg border border-border bg-panel-solid/70 p-6">
      <h1 className="text-2xl font-bold">Security Alerts</h1>
      <h2 className="mt-4 text-lg font-semibold text-primary">Governed Alert-Evidence Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard no longer polls an unsupported alert endpoint or displays alert identifiers, rule names, endpoint identifiers, severity, timestamps, or raw details. The direct client path did not establish the required authenticated tenant scope, analyst authorization, evidence provenance, response shape, data-minimization, or audit contract.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Core detection, correlation, and analyst workflow services remain separately protected. Any future dashboard integration must use tenant-scoped, authorization-checked, provenance-linked alert evidence; minimize sensitive fields; distinguish deterministic detections from analyst interpretation; retain auditable retrieval and lifecycle transitions; and remain non-enforcing with no containment or response authority.
      </p>
    </section>
  </div>
);

export default AlertsPage;
