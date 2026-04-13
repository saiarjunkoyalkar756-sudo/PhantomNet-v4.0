// phantomnet-website/app/about/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Target, Eye, Rocket, GitFork } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
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
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Reshaping Cyber Defense for a New Era</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto">
                        PhantomNet was founded on the belief that traditional cybersecurity models are failing
                        against the sophistication and scale of modern threats. We envision a world where
                        organizations are empowered by autonomous, AI-driven defenses that protect continuously,
                        adapt intelligently, and heal themselves.
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
                            To deliver a truly autonomous cyber defense platform that eliminates manual
                            security toil, provides real-time threat neutralization, and ensures the
                            uninterrupted resilience of enterprise operations worldwide. We empower
                            security teams to transcend reactive firefighting and focus on strategic defense.
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
                            A future where cyber threats are preemptively neutralized by self-healing systems,
                            where digital trust is absolute, and where security is an invisible, seamless
                            enabler of innovation, not a barrier. We envision a world where organizations can
                            operate with unwavering confidence in their digital security.
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
                        The cybersecurity industry is plagued by a growing skills gap, alert fatigue, and
                        a reactive security posture that consistently puts enterprises at risk. PhantomNet was
                        engineered to close these gaps, shifting the paradigm from human-centric response to
                        AI-driven autonomous protection. We exist to make advanced cyber defense accessible,
                        scalable, and effective for every organization.
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
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Open-Source Philosophy, Enterprise-Grade Execution</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-8">
                        PhantomNet embraces the collaborative power of the open-source community for certain core components,
                        fostering transparency and rapid innovation. This foundation is then hardened, scaled, and
                        augmented with proprietary AI and automation layers to deliver a secure, reliable, and
                        fully-supported enterprise solution. We offer the best of both worlds: community-driven
                        advancement and corporate-grade assurance.
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
