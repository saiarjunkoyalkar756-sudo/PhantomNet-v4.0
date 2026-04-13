// phantomnet-website/app/page.tsx
'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { AnimatedAttackFlow } from '@/components/AnimatedAttackFlow';

export default function HomePage() {
  return (
    <div className="relative overflow-hidden bg-pn-dark-blue text-pn-text-light">
      {/* Hero Section */}
      <section className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] text-center px-4 py-16 md:py-24">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-4xl md:text-6xl lg:text-7xl font-bold font-heading mb-6 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text leading-tight max-w-5xl"
        >
          Autonomous AI Cyber Defense for the Modern Enterprise
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-lg md:text-xl text-pn-text-muted mb-10 max-w-3xl"
        >
          PhantomNet delivers an AI-driven security operations platform that automatically detects, analyzes, and neutralizes cyber threats with unparalleled speed and precision.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 mb-16"
        >
          <Link href="/contact" className="px-8 py-3 bg-pn-neon-blue text-pn-dark-blue font-semibold rounded-md hover:bg-pn-electric-purple hover:text-pn-heading transition-all duration-300 text-lg shadow-lg">
            Request Demo
          </Link>
          <Link href="/architecture" className="px-8 py-3 border border-pn-neon-blue text-pn-neon-blue font-semibold rounded-md hover:bg-pn-neon-blue hover:text-pn-dark-blue transition-all duration-300 text-lg shadow-lg">
            View Architecture
          </Link>
        </motion.div>

        {/* Animated Attack Flow Visualization */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="w-full max-w-4xl"
        >
          <AnimatedAttackFlow />
        </motion.div>
      </section>

      {/* Placeholder for other sections */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold text-pn-heading mb-8">More sections to come...</h2>
        <p className="text-pn-text-muted">This is a placeholder for Platform Overview, Features, etc. that will be built on separate pages.</p>
      </section>
    </div>
  );
}