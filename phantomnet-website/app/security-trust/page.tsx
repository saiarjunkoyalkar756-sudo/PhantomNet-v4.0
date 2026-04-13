// phantomnet-website/app/security-trust/page.tsx
'use client';

import { motion } from 'framer-motion';
import {
    Shield,
    Lock,
    Key,
    Fingerprint,
    ScrollText,
    PowerOff, // For fail-fast
} from 'lucide-react';

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
};

export default function SecurityTrustPage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    Security & Trust
                </motion.h1>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Foundational Security for Enterprise Assurance</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-10">
                        At PhantomNet, security is not an afterthought; it's architected into every layer of our platform.
                        We provide an immutable, verifiable, and resilient defense posture that meets the stringent demands
                        of enterprise security and compliance.
                    </p>
                </motion.section>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16 md:mb-24">
                    {/* Zero Trust Design */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                    >
                        <Shield size={48} className="text-pn-neon-blue mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Zero Trust Design</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            PhantomNet embraces a Zero Trust architecture, verifying every user and device,
                            limiting access to only what's necessary, and authenticating every request,
                            regardless of network location. Trust is never assumed, always verified.
                        </p>
                    </motion.div>

                    {/* Encryption */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                    >
                        <Lock size={48} className="text-pn-electric-purple mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">End-to-End Encryption</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            All data, whether at rest or in transit, is protected with industry-leading encryption standards.
                            This ensures the confidentiality and integrity of your sensitive security telemetry and operational data
                            across the entire PhantomNet ecosystem.
                        </p>
                    </motion.div>

                    {/* RBAC */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                    >
                        <Key size={48} className="text-pn-neon-blue mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Granular Role-Based Access Control (RBAC)</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Define precise access permissions based on roles and responsibilities. Our granular RBAC
                            ensures that users only have access to the data and functionalities required for their duties,
                            minimizing the attack surface and upholding the principle of least privilege.
                        </p>
                    </motion.div>

                    {/* Auditability */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                    >
                        <Fingerprint size={48} className="text-pn-electric-purple mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Unquestionable Auditability</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Every action within PhantomNet, from data ingestion to autonomous response,
                            is logged and made available for detailed auditing. Combined with our Blockchain Audit Logs,
                            this provides an irrefutable record for investigations and compliance.
                        </p>
                    </motion.div>

                    {/* Compliance-Ready Messaging */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-neon-blue transition-all duration-300"
                    >
                        <ScrollText size={48} className="text-pn-neon-blue mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Compliance-Ready Operations</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            PhantomNet is designed with adherence to major regulatory frameworks in mind.
                            Our robust security controls and immutable auditing capabilities simplify
                            compliance with standards like GDPR, HIPAA, ISO 27001, and SOC 2.
                        </p>
                    </motion.div>

                    {/* SAFE_MODE Philosophy */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={cardVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border group hover:border-pn-electric-purple transition-all duration-300"
                    >
                        <PowerOff size={48} className="text-pn-electric-purple mb-4" />
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">SAFE_MODE Philosophy</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Embracing a "fail-fast, recover-strong" philosophy, PhantomNet is engineered to
                            detect and isolate failures instantly. This prevents cascading impacts and ensures
                            system integrity, avoiding "zombie systems" and maintaining continuous security
                            operations even under duress.
                        </p>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
