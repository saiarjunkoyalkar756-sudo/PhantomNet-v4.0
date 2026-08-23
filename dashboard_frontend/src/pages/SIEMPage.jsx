import React from 'react';

const SIEMPage = () => (
  <div className="p-4">
    <h1 className="text-2xl font-bold">SIEM</h1>
    <section className="mt-4 rounded-lg border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Log-Search Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard no longer sends queries to the retired PhantomQL service or displays raw log-search results. The previous direct localhost request was not a supported tenant-scoped analyst workflow and could not establish evidence provenance, authorization, or safe result handling.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        The separately protected threat-hunting capability remains the supported analysis boundary. Any future SIEM search integration must enforce tenant scope and analyst authorization, use evidence-linked query results, apply result minimization, and preserve deterministic auditability rather than exposing a direct legacy query endpoint.
      </p>
    </section>
  </div>
);

export default SIEMPage;
