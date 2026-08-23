import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const AttackGraphPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="h-full flex flex-col space-y-6"
  >
    <PageHeader
      title="ATTACK-PATH ANALYSIS"
      subtitle="Fixture lateral-movement graphs, risk assertions, segmentation findings, and node-containment controls are retired pending governed analysis and containment integration."
    />

    <section className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Attack-Path and Containment Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not display attack paths, relationship topology, asset risk, compromise status, segmentation violations, blast-radius estimates, or containment results. The legacy page used fixture data and local simulated isolation, which could be mistaken for tenant-authorized evidence or executed defensive action.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        The separately protected attack-path analysis and governed containment control planes remain the only supported boundaries. Any future dashboard integration must use tenant-scoped, provenance-linked results; distinguish graph hypotheses from verified evidence; and retain request, human approval, HMAC-signed audit, controlled execution, verification, and rollback without automatic high-impact containment.
      </p>
    </section>
  </MotionDiv>
);

export default AttackGraphPage;
