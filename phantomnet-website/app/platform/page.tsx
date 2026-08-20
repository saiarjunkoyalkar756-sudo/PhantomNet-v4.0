// phantomnet-website/app/platform/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Lightbulb, Shield, Zap } from 'lucide-react'; // Lucide icons for visual appeal

const featureVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
};

const iconVariants = {
    hidden: { scale: 0.8, opacity: 0 },
    visible: { scale: 1, opacity: 1, transition: { duration: 0.5, delay: 0.2 } },
};

export default function PlatformOverviewPage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    Platform Overview
                </motion.h1>

                {/* What PhantomNet Is */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={featureVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <motion.div variants={iconVariants} className="flex-shrink-0">
                            <Lightbulb size={64} className="text-pn-neon-blue" />
                        </motion.div>
                        <div>
                            <h2 className="text-3xl font-semibold font-heading mb-4 text-pn-heading">What is PhantomNet?</h2>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                PhantomNet is a self-hosted SOC foundation under active development. It connects canonical telemetry, governed correlation, tenant-owned evidence, case workflows, analyst context, and approval-bound response so teams can inspect and operate the security controls they rely on.
                            </p>
                        </div>
                    </div>
                </motion.section>

                {/* Problems It Solves */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={featureVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <div className="flex flex-col md:flex-row-reverse items-center gap-8">
                        <motion.div variants={iconVariants} className="flex-shrink-0">
                            <Shield size={64} className="text-pn-electric-purple" />
                        </motion.div>
                        <div>
                            <h2 className="text-3xl font-semibold font-heading mb-4 text-pn-heading">Problems PhantomNet Solves</h2>
                            <ul className="list-disc list-inside text-lg text-pn-text-muted leading-relaxed space-y-2">
                                <li>
                                    <strong className="text-pn-neon-blue">Alert Fatigue:</strong> Provides deterministic suppression controls, structured hunts, and evidence-to-decision traces for analyst review.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Response Governance:</strong> Supports approval-bound containment requests with signed audit, verification, and rollback evidence; it does not autonomously contain threats.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Complex Threat Landscape:</strong> Preserves canonical events, MITRE mappings, provenance, and graph context for repeatable investigation and detection engineering.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Talent Shortage:</strong> Gives analysts documented workflows, evidence context, and deterministic prioritization while keeping accountability with human operators.
                                </li>
                            </ul>
                        </div>
                    </div>
                </motion.section>

                {/* Why It's Different */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={featureVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <motion.div variants={iconVariants} className="flex-shrink-0">
                            <Zap size={64} className="text-pn-neon-blue" />
                        </motion.div>
                        <div>
                            <h2 className="text-3xl font-semibold font-heading mb-4 text-pn-heading">Why PhantomNet is Different</h2>
                            <p className="text-lg text-pn-text-muted leading-relaxed mb-4">
                                PhantomNet is differentiated by its evidence-first architecture and its refusal to bypass approval for high-impact action. It treats response as a governed lifecycle with explicit audit, verification, and rollback boundaries.
                            </p>
                            <ul className="list-disc list-inside text-lg text-pn-text-muted leading-relaxed space-y-2">
                                <li>
                                    <strong className="text-pn-neon-blue">Governed Response:</strong> High-impact actions require a recorded human approval, HMAC-signed audit evidence, adapter-specific verification, and governed rollback.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Read-Only Intelligence Context:</strong> Source-provenance intelligence can enrich evidence but cannot bypass correlation or response safeguards.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Staged Integrations:</strong> Endpoint, AWS, and Wazuh response paths remain disabled until their separate non-production validation gates are completed.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Tamper-Evident Audit Chain:</strong> Governed containment records form a verifiable HMAC-signed application audit chain; this is not presented as a distributed blockchain or compliance certification.
                                </li>
                            </ul>
                        </div>
                    </div>
                </motion.section>

                {/* AI-First Autonomous SOC Concept */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={featureVariants}
                    className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-4 text-center text-pn-heading">The Evidence-First SOC</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed text-center max-w-4xl mx-auto mb-8">
                        PhantomNet concentrates on reproducible security operations: observable ingestion, governed correlation, analyst review, and accountable response. AI-native assistance is a future advisory layer and cannot replace evidence or human approval.
                    </p>
                    <div className="grid md:grid-cols-3 gap-8 mt-8">
                        <div className="text-center">
                            <motion.div variants={iconVariants} className="flex justify-center mb-4">
                                <span className="p-4 rounded-full bg-pn-neon-blue/20 text-pn-neon-blue inline-block">
                                    <Lightbulb size={48} />
                                </span>
                            </motion.div>
                            <h3 className="text-xl font-semibold font-heading mb-2 text-pn-heading">Observable Workflows</h3>
                            <p className="text-pn-text-muted text-base">Health, readiness, evidence, audit, and analyst-context controls can be inspected and validated by operators.</p>
                        </div>
                        <div className="text-center">
                            <motion.div variants={iconVariants} className="flex justify-center mb-4">
                                <span className="p-4 rounded-full bg-pn-electric-purple/20 text-pn-electric-purple inline-block">
                                    <Zap size={48} />
                                </span>
                            </motion.div>
                            <h3 className="text-xl font-semibold font-heading mb-2 text-pn-heading">Accountable Response</h3>
                            <p className="text-pn-text-muted text-base">Containment remains approval-bound, verified, rollback-capable, and disabled by default until validated.</p>
                        </div>
                        <div className="text-center">
                            <motion.div variants={iconVariants} className="flex justify-center mb-4">
                                <span className="p-4 rounded-full bg-pn-neon-blue/20 text-pn-neon-blue inline-block">
                                    <Shield size={48} />
                                </span>
                            </motion.div>
                            <h3 className="text-xl font-semibold font-heading mb-2 text-pn-heading">Evidence-Led Improvement</h3>
                            <p className="text-pn-text-muted text-base">Rules, fixtures, baselines, and lab evidence define what can be improved and what remains a roadmap item.</p>
                        </div>
                    </div>
                </motion.section>
            </div>
        </div>
    );
}
