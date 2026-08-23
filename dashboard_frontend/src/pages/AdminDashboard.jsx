import React from 'react';

const AdminDashboard = () => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-primary">Administration</h1>
    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Administration Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not poll alert data, count active agents or users, report system health, or provide administrative action shortcuts. The prior view combined an unsupported alert endpoint with hard-coded deployment counts and an unverified operational-status assertion.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future administration surface must enforce authenticated role and tenant scope; use authorization-checked, provenance-linked, minimized data; distinguish readiness signals from production availability; audit all changes; and keep high-impact actions within their separately governed approval, audit, verification, and rollback lifecycles.
      </p>
    </section>
  </div>
);

export default AdminDashboard;
