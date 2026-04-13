import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Bot, MessageSquare } from 'lucide-react';
import TerminalChat from '@/features/ai-console/components/TerminalChat';

const AIConsole = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="AI CONSOLE"
        subtitle="Interact with PhantomNet's AI Security Analyst."
        actions={
            <div className="flex items-center space-x-2">
                <Bot className="text-primary animate-bounce" size={20} />
                <span className="text-primary font-mono text-sm">ONLINE</span>
            </div>
        }
      />
      {/* Content for AI Console */}
      <div className="bg-panel-solid/70 backdrop-blur-md border border-border rounded-xl p-6 flex-1 min-h-0">
        <TerminalChat />
      </div>
    </motion.div>
  );
};

export default AIConsole;
