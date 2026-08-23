import React from 'react';

const NetworkOverviewPage = () => (
  <div className="p-4 md:p-8">
    <h1 className="text-3xl font-bold mb-6">Network Overview</h1>
    <section className="rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Network-Evidence Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not connect to a network WebSocket or display real-time traffic, active connections, anomaly counts, or blocked-threat metrics. The prior client accepted unscoped stream messages and calculated security-relevant totals without authenticated tenant scope, source provenance, data validation, analyst authorization, or an evidence contract.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future network view must use a protected tenant-scoped analyst workflow with authorization-checked, provenance-linked, validated and minimized observations; identify data currency and collection boundaries; distinguish network observations from verified detections; retain deterministic auditability; and remain read-only and non-enforcing. It must not imply live network visibility, threat blocking, automatic containment, or response execution.
      </p>
    </section>
  </div>
);

export default NetworkOverviewPage;
