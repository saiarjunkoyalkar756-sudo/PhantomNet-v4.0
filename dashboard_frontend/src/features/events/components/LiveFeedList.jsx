import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

const LiveFeedList = ({ events, onEventClick }) => { // Now accepts events as a prop
  const feedRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom on new events
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [events]);

  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'High': return 'text-destructive';
      case 'Medium': return 'text-secondary';
      case 'Low': return 'text-primary';
      case 'Informational': return 'text-text-secondary';
      default: return 'text-text-secondary';
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, height: 0, marginBottom: 0 }
  };

  return (
    <div className="flex flex-col h-full bg-background rounded-lg border border-border overflow-hidden">
      <div className="flex items-center p-3 border-b border-border bg-panel-solid">
        <Terminal className="text-primary mr-2 animate-pulse" size={18} />
        <span className="font-mono text-primary text-sm">LIVE EVENT FEED</span>
      </div>
      <motion.div
        ref={feedRef}
        className="flex-1 overflow-y-auto custom-scrollbar p-3 font-mono text-sm"
      >
        <AnimatePresence initial={false}>
          {events.map((event) => (
            <motion.div
              key={event.id}
              variants={itemVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              layout
              transition={{ duration: 0.3 }}
              className="py-1 px-2 border-b border-border-light cursor-pointer hover:bg-accent/10 flex flex-col md:flex-row md:items-center justify-between"
              onClick={() => onEventClick(event)}
            >
              <div className="flex items-center flex-wrap">
                <span className="text-muted-foreground mr-2 whitespace-nowrap">[{new Date(event.timestamp).toLocaleTimeString()}]</span>
                <span className={cn("font-bold mr-2 whitespace-nowrap", getSeverityClass(event.severity))}>
                  {event.severity.toUpperCase()}
                </span>
                <span className="text-text-primary mr-2 flex-grow">{event.message}</span>
              </div>
              {event.aiInsight && (
                <span className="text-primary text-xs italic ml-auto md:ml-0 md:pl-4 whitespace-nowrap">
                  AI Insight
                </span>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default LiveFeedList;
