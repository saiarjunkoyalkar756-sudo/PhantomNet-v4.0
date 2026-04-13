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
                                PhantomNet is a cutting-edge, AI-driven platform that revolutionizes cybersecurity operations.
                                It integrates advanced artificial intelligence with autonomous response capabilities to create
                                a self-healing security ecosystem. Unlike traditional Security Information and Event Management (SIEM)
                                systems, PhantomNet operates with real-time threat detection and automated remediation,
                                minimizing human intervention and maximizing defense efficacy.
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
                                    <strong className="text-pn-neon-blue">Alert Fatigue:</strong> Automates triage and response, drastically reducing the volume of alerts for human analysts.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Slow Response Times:</strong> Provides real-time, autonomous threat containment and remediation, measured in seconds, not hours or days.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Complex Threat Landscape:</strong> Leverages AI to detect sophisticated, evolving threats that bypass traditional signature-based defenses.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Talent Shortage:</strong> Augments existing security teams, allowing them to do more with less by automating routine and complex tasks.
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
                                PhantomNet stands apart with its truly autonomous capabilities and a proactive, AI-first philosophy.
                                We don't just alert; we act. Our platform is built from the ground up for self-governing security.
                            </p>
                            <ul className="list-disc list-inside text-lg text-pn-text-muted leading-relaxed space-y-2">
                                <li>
                                    <strong className="text-pn-neon-blue">Autonomous Response:</strong> Beyond SOAR, our AI executes complex defensive actions without direct human oversight.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Predictive Threat Intelligence:</strong> Foresees potential attacks by analyzing behavioral patterns and global threat data.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Self-Healing Infrastructure:</strong> Agents can automatically patch vulnerabilities or reconfigure systems in response to threats.
                                </li>
                                <li>
                                    <strong className="text-pn-neon-blue">Blockchain Audit Trail:</strong> Ensures every action and event is immutably recorded for unparalleled integrity and compliance.
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
                    <h2 className="text-3xl font-semibold font-heading mb-4 text-center text-pn-heading">The AI-First Autonomous SOC</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed text-center max-w-4xl mx-auto mb-8">
                        PhantomNet embodies the future of security operations, where AI is not just an additive feature, but the core
                        driving force. Our autonomous SOC concept shifts from reactive human-centric models to a proactive,
                        AI-powered defense that continuously adapts, learns, and protects your enterprise.
                    </p>
                    <div className="grid md:grid-cols-3 gap-8 mt-8">
                        <div className="text-center">
                            <motion.div variants={iconVariants} className="flex justify-center mb-4">
                                <span className="p-4 rounded-full bg-pn-neon-blue/20 text-pn-neon-blue inline-block">
                                    <Lightbulb size={48} />
                                </span>
                            </motion.div>
                            <h3 className="text-xl font-semibold font-heading mb-2 text-pn-heading">Continuous Vigilance</h3>
                            <p className="text-pn-text-muted text-base">24/7 AI monitoring and analysis, far beyond human capacity.</p>
                        </div>
                        <div className="text-center">
                            <motion.div variants={iconVariants} className="flex justify-center mb-4">
                                <span className="p-4 rounded-full bg-pn-electric-purple/20 text-pn-electric-purple inline-block">
                                    <Zap size={48} />
                                </span>
                            </motion.div>
                            <h3 className="text-xl font-semibold font-heading mb-2 text-pn-heading">Automated Remediation</h3>
                            <p className="text-pn-text-muted text-base">Threats are neutralized instantly and automatically.</p>
                        </div>
                        <div className="text-center">
                            <motion.div variants={iconVariants} className="flex justify-center mb-4">
                                <span className="p-4 rounded-full bg-pn-neon-blue/20 text-pn-neon-blue inline-block">
                                    <Shield size={48} />
                                </span>
                            </motion.div>
                            <h3 className="text-xl font-semibold font-heading mb-2 text-pn-heading">Adaptive Defense</h3>
                            <p className="text-pn-text-muted text-base">AI learns from every incident, strengthening defenses over time.</p>
                        </div>
                    </div>
                </motion.section>
            </div>
        </div>
    );
}
