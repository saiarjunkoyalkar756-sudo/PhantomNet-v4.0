import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

const LogStreamViewer = ({ logs, format }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [logs]);

  const formatLog = (logEntry) => {
    if (format === 'formatted') {
      try {
        const parsed = JSON.parse(logEntry);
        return JSON.stringify(parsed, null, 2);
      } catch (e) {
        // Not a JSON, return as is
        return logEntry;
      }
    }
    return logEntry;
  };

  const getLogLineClass = (logEntry) => {
    // Basic severity-like highlighting for demonstration
    if (logEntry.includes('ERROR') || logEntry.includes('CRITICAL')) return 'text-destructive';
    if (logEntry.includes('WARNING')) return 'text-secondary';
    if (logEntry.includes('INFO')) return 'text-primary';
    return 'text-text-primary';
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, height: 0 },
  };

  return (
    <div className="flex flex-col h-full bg-background rounded-lg border border-border overflow-hidden font-mono text-sm">
      <ScrollArea className="flex-1 p-3">
        <div ref={scrollRef}>
          <AnimatePresence initial={false}>
            {logs.map((log, index) => (
              <motion.pre
                key={index} // Using index as key, consider unique ID for real logs
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                layout
                transition={{ duration: 0.3 }}
                className={cn('whitespace-pre-wrap py-0.5', getLogLineClass(log))}
              >
                {formatLog(log)}
              </motion.pre>
            ))}
          </AnimatePresence>
        </div>
      </ScrollArea>
    </div>
  );
};

export default LogStreamViewer;
