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
} from 'lucide-react';

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } },
};

const featureCardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' as const } },
};

export default function FeaturesPage() {
    const features = [
        {
            title: 'Canonical Telemetry Ingestion',
            description: 'Normalize supported endpoint and Wazuh telemetry into a versioned canonical event contract. Source adapters are tenant-scoped, evidence-preserving, and validated through controlled integration paths.',
            icon: CloudUpload,
        },
        {
            title: 'Governed Detection Engineering',
            description: 'Use versioned deterministic correlation rules, offline fixtures, MITRE coverage evidence, and bounded analyst-alert suppression. Advisory AI-assisted rule drafting remains a roadmap capability and cannot execute response.',
            icon: BrainCircuit,
        },
        {
            title: 'Read-Only Intelligence Context',
            description: 'Attach tenant-scoped, provenance-preserving intelligence context to investigation evidence. Enrichment remains read-only and cannot bypass correlation, approval, or containment safeguards.',
            icon: Eye,
        },
        {
            title: 'Governed Response Workflow',
            description: 'Create approval-bound containment requests with HMAC-signed audit evidence, adapter-specific verification, and governed rollback. High-impact actions are never automatic and remain disabled until separately validated.',
            icon: Zap,
        },
        {
            title: 'Tamper-Evident Audit Chain',
            description: 'Containment lifecycle records form a tenant-scoped HMAC-signed hash chain that can be verified after execution, rollback, and recovery. It is an application-level tamper-evident audit control, not a distributed blockchain.',
            icon: ScrollText,
        },
        {
            title: 'Agent Security Boundaries',
            description: 'Agent and endpoint integrations use explicit identity, integrity, and telemetry boundaries. Deployment-specific controls must be staged and independently validated before they are relied upon in an operational environment.',
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
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Evidence-First SOC Building Blocks</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-10">
                        PhantomNet is a self-hosted SOC foundation under active development. The platform distinguishes implemented and tested controls from lab-validation gates and future roadmap capabilities.
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
