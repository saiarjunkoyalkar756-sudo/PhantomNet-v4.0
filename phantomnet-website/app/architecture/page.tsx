// phantomnet-website/app/architecture/page.tsx
'use client';

import { motion } from 'framer-motion';
import { ArchitectureDiagram } from '@/components/ArchitectureDiagram';
import { Fingerprint, Cloud, GitBranch, ShieldPlus } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
};

export default function ArchitecturePage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    PhantomNet Architecture
                </motion.h1>

                {/* Interactive Architecture Diagram */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">A Resilient & Scalable Foundation</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-10">
                        PhantomNet's architecture is engineered for maximum resilience, scalability, and security.
                        Built on a foundation of loosely coupled microservices, it processes billions of events
                        daily, providing real-time autonomous cyber defense.
                    </p>
                    <ArchitectureDiagram />
                    <p className="text-sm text-pn-text-muted mt-8">Hover over components for conceptual details (future interaction).</p>
                </motion.section>

                {/* Event Flow Explanation */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-center text-pn-heading">The Autonomous Event Flow</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed text-center max-w-4xl mx-auto mb-10">
                        Our event-driven pipeline ensures every security event is processed, analyzed, and acted upon
                        with lightning speed, creating a truly self-healing defense mechanism.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            { title: 'Agent Deployment', description: 'Lightweight agents collect telemetry from diverse endpoints and infrastructure.', icon: <Fingerprint size={24} /> },
                            { title: 'Telemetry Ingestion', description: 'Raw data is securely ingested and normalized into a unified format.', icon: <Cloud size={24} /> },
                            { title: 'AI-Powered Analysis', description: 'Advanced AI engines detect anomalies, threats, and behavioral deviations.', icon: <ShieldPlus size={24} /> },
                            { title: 'Threat Correlation', description: 'AI correlates events with global and custom threat intelligence.', icon: <GitBranch size={24} /> },
                            { title: 'Autonomous SOAR', description: 'Orchestrated playbooks execute containment and remediation actions.', icon: <Zap size={24} /> },
                            { title: 'Blockchain Audit', description: 'All actions and events are immutably logged for integrity and compliance.', icon: <Book size={24} /> },
                        ].map((item, index) => (
                            <motion.div
                                key={index}
                                variants={cardVariants}
                                className="flex items-start p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                            >
                                <div className="p-3 rounded-full bg-pn-neon-blue/20 text-pn-neon-blue mr-4">
                                    {item.icon}
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold text-pn-heading mb-2">{item.title}</h3>
                                    <p className="text-base text-pn-text-muted">{item.description}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </motion.section>

                {/* Key Architectural Principles */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-center text-pn-heading">Key Architectural Principles</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <motion.div variants={cardVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-electric-purple transition-all duration-300">
                            <h3 className="text-2xl font-semibold text-pn-heading mb-3 flex items-center">
                                <ShieldPlus size={28} className="text-pn-electric-purple mr-3" />
                                Zero Trust Architecture
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                Our entire platform operates on a Zero Trust model: never trust, always verify.
                                This ensures that every component, user, and service is authenticated and authorized,
                                irrespective of its location within or outside the network perimeter.
                            </p>
                        </motion.div>
                        <motion.div variants={cardVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-neon-blue transition-all duration-300">
                            <h3 className="text-2xl font-semibold text-pn-heading mb-3 flex items-center">
                                <Cloud size={28} className="text-pn-neon-blue mr-3" />
                                Event-Driven Design with Kafka
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                At the heart of PhantomNet is a high-throughput, fault-tolerant event streaming
                                architecture powered by Apache Kafka. All security events and system telemetry
                                flow through Kafka, enabling real-time processing and decoupling of services.
                            </p>
                        </motion.div>
                        <motion.div variants={cardVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-electric-purple transition-all duration-300">
                            <h3 className="text-2xl font-semibold text-pn-heading mb-3 flex items-center">
                                <GitBranch size={28} className="text-pn-electric-purple mr-3" />
                                Scalable Microservices
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                PhantomNet is built as a collection of independent, deployable microservices.
                                This modular approach allows for extreme scalability, rapid feature development,
                                and high availability, ensuring our platform can meet enterprise demands.
                            </p>
                        </motion.div>
                        <motion.div variants={cardVariants} className="p-6 bg-pn-dark-blue rounded-lg shadow-md border border-pn-border group hover:border-pn-neon-blue transition-all duration-300">
                            <h3 className="text-2xl font-semibold text-pn-heading mb-3 flex items-center">
                                <Fingerprint size={28} className="text-pn-neon-blue mr-3" />
                                Secure & Resilient APIs
                            </h3>
                            <p className="text-lg text-pn-text-muted leading-relaxed">
                                All internal and external communications within PhantomNet are secured via
                                authenticated and authorized APIs, enforcing strong access controls and
                                encryption to protect sensitive security data at rest and in transit.
                            </p>
                        </motion.div>
                    </div>
                </motion.section>
            </div>
        </div>
    );
}
