// phantomnet-website/app/roadmap/page.tsx
'use client';

import { motion } from 'framer-motion';
import { CheckCircle, Hourglass, TrendingUp, Calendar, BoxSelect } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

export default function RoadmapPage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    Demo & Roadmap
                </motion.h1>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">See PhantomNet Today, Plan for Tomorrow</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto">
                        PhantomNet is continuously evolving to meet the dynamic challenges of the cyber landscape.
                        Explore our current capabilities and get a glimpse into the future of autonomous cyber defense
                        with our transparent product roadmap.
                    </p>
                </motion.section>

                {/* What Works Today */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-8 text-center text-pn-heading">What Works Today</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            'Real-time Telemetry Ingestion & Normalization',
                            'AI-Powered Behavioral Anomaly Detection',
                            'Automated Threat Intelligence Correlation',
                            'Basic SOAR Playbook Execution (Containment)',
                            'Immutable Blockchain Audit Logging',
                            'Secure Agent Deployment & Integrity Checks',
                        ].map((item, index) => (
                            <motion.div
                                key={index}
                                variants={itemVariants}
                                className="flex items-center p-4 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                            >
                                <CheckCircle size={24} className="text-pn-neon-blue mr-3" />
                                <p className="text-lg text-pn-text-light">{item}</p>
                            </motion.div>
                        ))}
                    </div>
                </motion.section>

                {/* What's In Progress */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-8 text-center text-pn-heading">What's In Progress</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            'Advanced Predictive Threat Forecasting',
                            'Dynamic Incident Response Workflows (SOAR)',
                            'Explainable AI (XAI) for Alert Context',
                            'Multi-Cloud Security Posture Management',
                            'Advanced Agent Self-Healing Capabilities',
                            'Customizable Reporting & Dashboarding',
                        ].map((item, index) => (
                            <motion.div
                                key={index}
                                variants={itemVariants}
                                className="flex items-center p-4 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                            >
                                <Hourglass size={24} className="text-pn-electric-purple mr-3" />
                                <p className="text-lg text-pn-text-light">{item}</p>
                            </motion.div>
                        ))}
                    </div>
                </motion.section>

                {/* 3-6 Month Roadmap */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-8 text-center text-pn-heading">3-6 Month Roadmap Highlights</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <motion.div variants={itemVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-neon-blue transition-all duration-300">
                            <h3 className="text-2xl font-semibold font-heading mb-3 flex items-center">
                                <TrendingUp size={28} className="text-pn-neon-blue mr-3" />
                                Enhanced Threat Remediation
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                Expanding autonomous remediation capabilities to include more complex
                                system reconfigurations and automated patching integrations.
                            </p>
                        </motion.div>
                        <motion.div variants={itemVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-electric-purple transition-all duration-300">
                            <h3 className="text-2xl font-semibold font-heading mb-3 flex items-center">
                                <BoxSelect size={28} className="text-pn-electric-purple mr-3" />
                                Integrated Vulnerability Management
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                Seamless integration with vulnerability scanners to automate discovery,
                                prioritization, and mitigation of security weaknesses.
                            </p>
                        </motion.div>
                        <motion.div variants={itemVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-neon-blue transition-all duration-300">
                            <h3 className="text-2xl font-semibold font-heading mb-3 flex items-center">
                                <Calendar size={28} className="text-pn-neon-blue mr-3" />
                                Compliance Framework Automation
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                Automated reporting and evidence collection tailored for specific regulatory
                                compliance frameworks.
                            </p>
                        </motion.div>
                        <motion.div variants={itemVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-electric-purple transition-all duration-300">
                            <h3 className="text-2xl font-semibold font-heading mb-3 flex items-center">
                                <Lightbulb size={28} className="text-pn-electric-purple mr-3" />
                                AI-Driven Attack Surface Management
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                Continuously discover and assess an organization's external attack surface
                                using AI to identify potential exposure points.
                            </p>
                        </motion.div>
                    </div>
                </motion.section>
            </div>
        </div>
    );
}
