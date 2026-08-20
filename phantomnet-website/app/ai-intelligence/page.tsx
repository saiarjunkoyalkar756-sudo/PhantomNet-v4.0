// phantomnet-website/app/ai-intelligence/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Brain, TrendingUp, GitFork, MessageSquare } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } },
};

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' as const } },
};

export default function AIIntelligencePage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    AI & Intelligence
                </motion.h1>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Evidence-Grounded Detection and Advisory Intelligence</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-10">
                        PhantomNet currently provides deterministic correlation, versioned rule governance, MITRE evidence, and analyst decision traces. AI-assisted triage and rule drafting are planned as advisory workflows that must remain evidence-grounded, reviewable, and unable to execute containment.
                    </p>
                </motion.section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16 md:mb-24">
                    {/* Behavioral AI */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                    >
                        <Brain size={48} className="text-pn-neon-blue mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Versioned Detection Rules</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Correlation rules are versioned, tenant-scoped, fixture-tested, and mapped to MITRE evidence. They emit analyst evidence deterministically and do not claim universal behavioral baselining or zero-day detection coverage.
                        </p>
                    </motion.div>

                    {/* Threat Forecasting */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                    >
                        <TrendingUp size={48} className="text-pn-electric-purple mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Read-Only Intelligence Context</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Integrated evidence preserves source provenance and can enrich investigation context through explicitly configured, read-only integrations. Forecasting and broad global-feed coverage are not represented as implemented capabilities.
                        </p>
                    </motion.div>

                    {/* Correlation Engine */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                    >
                        <GitFork size={48} className="text-pn-neon-blue mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Evidence-to-Decision Context</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Analysts can inspect tenant-bound alerts, detections, cases, evidence, graph context, and deterministic priority factors. Performance claims are limited to published benchmark evidence; the platform does not claim to eliminate false positives.
                        </p>
                    </motion.div>

                    {/* Explainability */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                    >
                        <MessageSquare size={48} className="text-pn-electric-purple mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Explainable Analyst Review</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Alert and case decision traces show the identifiers and factors used to construct an analyst review view. Any future AI suggestion must expose its supporting evidence, remain subject to human review, and never create or execute containment on its own.
                        </p>
                    </motion.div>
                </div>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Evidence Before Intelligence Claims</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto">
                        The current platform makes claims only for implemented controls with regression or lab evidence. AI-native assistance is a roadmap direction: it will be evaluated against explicit fixtures and analyst-review gates before it is positioned as an operational capability.
                    </p>
                </motion.section>

            </div>
        </div>
    );
}
