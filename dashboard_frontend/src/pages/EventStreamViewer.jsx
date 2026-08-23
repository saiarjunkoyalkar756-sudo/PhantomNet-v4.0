import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const EventStreamViewer = () => (
  <div className="font-sans h-full flex flex-col">
    <PageHeader
      title="EVENT EVIDENCE"
      subtitle="Governed event-evidence integration is pending."
    />
    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Event-Evidence Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not connect to an event WebSocket, receive a live feed, retain events in browser state, filter endpoint data, or expose raw event details. The prior client accepted unscoped stream messages without authenticated tenant scope, source provenance, message validation, analyst authorization, data minimization, or an auditable evidence contract.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        Any future event view must use a protected tenant-scoped analyst workflow with authorization-checked, provenance-linked, validated and minimized observations; constrain filters and returned fields; retain deterministic auditability; and distinguish collected telemetry from verified detections. It must remain read-only and non-enforcing, with no containment or response authority.
      </p>
    </section>
  </div>
);

export default EventStreamViewer;
