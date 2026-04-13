// phantomnet-website/app/features/page.tsx
'use client';

import { motion } from 'framer-motion';
import {
    CloudUpload,
    BrainCircuit,
    Eye,
    Zap,
    ScrollText,
    ShieldCheck,
    Lock, // For mTLS
    Fingerprint, // For integrity checks
} from 'lucide-react';

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const featureCardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
};

export default function FeaturesPage() {
    const features = [
        {
            title: 'Telemetry Ingestion',
            description: 'Ingest security telemetry from diverse sources – endpoints, cloud, network, applications – at hyperscale. Our intelligent collectors normalize data for unified analysis, ensuring no blind spots in your defense.',
            icon: CloudUpload,
        },
        {
            title: 'AI Behavioral Detection',
            description: 'Leverage advanced AI and machine learning to establish behavioral baselines for every entity. Detect anomalous activities, insider threats, and zero-day attacks that bypass traditional signature-based methods in real-time.',
            icon: BrainCircuit,
        },
        {
            title: 'Threat Intelligence Correlation',
            description: 'Automatically correlate internal security events with a vast network of global, real-time threat intelligence feeds. Proactively identify known bad actors, indicators of compromise (IOCs), and attack campaigns targeting your industry.',
            icon: Eye,
        },
        {
            title: 'SOAR Automation & Orchestration',
            description: 'Automate repetitive security tasks, orchestrate complex incident response playbooks, and accelerate threat containment and remediation. PhantomNet\'s SOAR capabilities empower your team to respond at machine speed.',
            icon: Zap,
        },
        {
            title: 'Blockchain Audit Logs',
            description: 'Ensure the undeniable integrity and immutability of all security events and actions. Our blockchain-powered audit trail provides cryptographic proof, making logs tamper-proof and compliance-ready for stringent regulatory requirements.',
            icon: ScrollText,
        },
        {
            title: 'Agent Security & Integrity',
            description: 'PhantomNet agents are built with robust security measures, including Mutual TLS (mTLS) for secure communication and continuous integrity checks to prevent tampering or compromise, ensuring the trustworthiness of your data sources.',
            icon: ShieldCheck,
        },
    ];

    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    Platform Features
                </motion.h1>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Comprehensive Capabilities for Total Cyber Resilience</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-10">
                        PhantomNet provides a suite of enterprise-grade features designed to give your organization
                        unparalleled visibility, detection, and autonomous response capabilities across your entire digital estate.
                    </p>
                </motion.section>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            initial="hidden"
                            whileInView="visible"
                            viewport={{ once: true, amount: 0.3 }}
                            variants={featureCardVariants}
                            className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                        >
                            <div className="flex items-center mb-4">
                                <feature.icon size={36} className="text-pn-neon-blue group-hover:text-pn-electric-purple transition-colors duration-300 mr-4" />
                                <h3 className="text-xl font-semibold font-heading text-pn-heading">{feature.title}</h3>
                            </div>
                            <p className="text-base text-pn-text-muted leading-relaxed">{feature.description}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
