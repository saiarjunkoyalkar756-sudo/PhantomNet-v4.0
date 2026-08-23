import { motion } from 'framer-motion';
import React from 'react';
import PageHeader from '@/components/shared/PageHeader';

const MotionDiv = motion.div;

const ThreatIntelOSINTPage = () => (
  <MotionDiv
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="font-sans h-full flex flex-col"
  >
    <PageHeader
      title="THREAT INTELLIGENCE"
      subtitle="Fixture OSINT lookup outputs, reputation scores, geolocation claims, IOC lists, and evidence timelines are retired pending governed advisory-enrichment integration."
    />

    <section className="mt-6 rounded-xl border border-border bg-panel-solid/70 p-6">
      <h2 className="text-lg font-semibold text-primary">Governed Advisory-Enrichment Integration Pending</h2>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        This dashboard does not perform indicator lookups or present reputation, malicious-report, geographic, provider, indicator, or timeline data. The prior local interaction generated randomized and fixture values that could be mistaken for sourced security evidence.
      </p>
      <p className="mt-3 text-sm text-text-secondary leading-6">
        The separately protected threat-intelligence service remains the supported advisory boundary. Any future dashboard integration must require analyst authorization, constrain and validate indicator input, preserve tenant scope and evidence provenance, minimize displayed provider data, expose availability without provider exception detail, and remain advisory-only with no response authority.
      </p>
    </section>
  </MotionDiv>
);

export default ThreatIntelOSINTPage;
