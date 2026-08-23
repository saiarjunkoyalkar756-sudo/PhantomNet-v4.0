import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const GraphInvestigationPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="GRAPH INVESTIGATION"
      subtitle="Direct arbitrary graph queries and raw result disclosure are retired pending governed investigation integration."
    />

    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Graph-Investigation Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not accept Cypher or other arbitrary graph queries, execute graph searches, or render raw relationship results. The prior client targeted the retired raw-graph endpoint and bypassed the required tenant scope, analyst authorization, evidence provenance, query constraints, and result-minimization controls.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        The separately protected governed graph and attack-path APIs remain the supported read-only investigation boundaries. Any future dashboard integration must use tenant-scoped, authorization-checked, provenance-linked results; expose only safe structured investigation inputs; minimize returned evidence; distinguish graph hypotheses from verified findings; and remain non-enforcing with no containment or response authority.
      </p>
    </section>
  </MotionDiv>
);

export default GraphInvestigationPage;
