// phantomnet-website/app/about/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Target, Eye, Rocket, GitFork } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } },
};

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' as const } },
};

export default function AboutPage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    About PhantomNet
                </motion.h1>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Building a Verifiable Self-Hosted SOC</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto">
                        PhantomNet is being built for teams that need an inspectable, self-hosted security operations foundation without vendor lock-in. Its design prioritizes tenant-owned evidence, deterministic detection, analyst context, and human-governed response over unverifiable automation claims.
                    </p>
                </motion.section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16 md:mb-24">
                    {/* Our Mission */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                    >
                        <Target size={48} className="text-pn-neon-blue mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Our Mission</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            To deliver composable security operations controls that teams can inspect, test, and operate themselves. PhantomNet aims to reduce repetitive investigative work with evidence, workflow, and advisory assistance while preserving accountable human decisions for high-impact action.
                        </p>
                    </motion.div>

                    {/* Our Vision */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                    >
                        <Eye size={48} className="text-pn-electric-purple mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Our Vision</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            A future where smaller teams can own their telemetry, detections, investigations, and response evidence. The platform vision is transparent, composable security operations with measurable validation gates—not an assertion that threats can be autonomously neutralized.
                        </p>
                    </motion.div>
                </div>

                {/* Why PhantomNet Exists */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Why PhantomNet Exists</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-8">
                        The cybersecurity industry is plagued by a growing skills gap, alert fatigue, and fragmented tooling. PhantomNet is engineered to connect canonical evidence, governed correlation, analyst context, and audited response workflows while keeping response authority with accountable operators.
                    </p>
                    <div className="flex justify-center mt-8">
                        <motion.div variants={cardVariants}>
                            <Rocket size={64} className="text-pn-neon-blue" />
                        </motion.div>
                    </div>
                </motion.section>

                {/* Open-source + Enterprise Positioning */}
                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Open-Source Philosophy, Evidence-First Execution</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-8">
                        PhantomNet embraces an inspectable development process, reproducible tests, and explicit operational runbooks. Capabilities are documented as implemented, lab-validated, or roadmap work so operators can make decisions from evidence rather than unsupported assurance claims.
                    </p>
                    <div className="flex justify-center mt-8">
                        <motion.div variants={cardVariants}>
                            <GitFork size={64} className="text-pn-electric-purple" />
                        </motion.div>
                    </div>
                </motion.section>
            </div>
        </div>
    );
}
