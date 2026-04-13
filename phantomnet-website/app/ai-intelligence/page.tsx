// phantomnet-website/app/ai-intelligence/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Brain, TrendingUp, GitFork, MessageSquare } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
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
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Beyond Signatures: True AI-Driven Cyber Defense</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto mb-10">
                        PhantomNet's core strength lies in its sophisticated AI engine, designed not just to detect,
                        but to understand, predict, and autonomously respond to the most advanced cyber threats.
                        We harness the power of machine learning, behavioral analytics, and real-time data
                        processing to deliver intelligence that truly matters.
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
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Behavioral AI</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Our AI baselines normal user and system behavior across your entire infrastructure.
                            Any deviation, no matter how subtle, is immediately flagged and analyzed for malicious intent.
                            This allows us to detect zero-day threats, insider threats, and sophisticated attacks that
                            evade traditional signature-based detection methods. We focus on patterns, not just payloads.
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
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Threat Forecasting</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            Leveraging global threat intelligence feeds, historical attack data, and predictive analytics,
                            PhantomNet forecasts potential attack vectors and vulnerabilities specific to your environment.
                            This enables proactive defense strategies, allowing your security posture to evolve
                            ahead of emerging threats.
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
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Correlation Engine</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            PhantomNet's advanced correlation engine processes millions of events per second,
                            identifying complex attack chains and linking seemingly disparate activities into
                            cohesive incident narratives. This contextual awareness eliminates false positives
                            and provides a clear, actionable picture of actual threats.
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
                        <h3 className="text-2xl font-semibold font-heading mb-3 text-pn-heading">Explainable AI (XAI)</h3>
                        <p className="text-lg text-pn-text-muted leading-relaxed">
                            We believe in transparency. PhantomNet's AI provides clear, concise explanations for
                            why an alert was generated or an autonomous action was taken. This explainability empowers
                            security analysts to understand the AI's reasoning, validate its decisions, and build trust
                            in the autonomous defense system. No black boxes, just verifiable intelligence.
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
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Realistic Intelligence, Not Hype</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto">
                        PhantomNet focuses on practical, deployable AI that delivers tangible security outcomes.
                        We avoid unverified claims and buzzwords, instead offering a robust, scientifically-backed
                        approach to autonomous cyber defense that CISOs can trust. Our intelligence augments
                        your team, allowing them to scale their expertise and respond effectively.
                    </p>
                </motion.section>

            </div>
        </div>
    );
}
