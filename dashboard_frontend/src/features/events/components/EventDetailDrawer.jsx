import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle, Info, Shield, Wifi } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

const EventDetailDrawer = ({ event, onClose }) => {
  if (!event) return null;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'High': return 'text-destructive';
      case 'Medium': return 'text-secondary';
      case 'Low': return 'text-primary';
      case 'Informational': return 'text-text-secondary';
      default: return 'text-text-secondary';
    }
  };

  return (
    <AnimatePresence>
      {event && (
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed inset-y-0 right-0 w-full md:w-1/3 bg-panel-solid backdrop-blur-lg border-l border-border shadow-2xl z-50 flex flex-col font-mono"
        >
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h2 className="text-xl font-bold text-text-primary flex items-center">
              <AlertTriangle className={cn("mr-2", getSeverityColor(event.severity))} size={24} />
              EVENT DETAILS
            </h2>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="text-text-secondary hover:text-primary" />
            </Button>
          </div>

          <div className="p-4 overflow-y-auto flex-1">
            <div className="mb-4">
              <p className="text-muted-foreground text-sm">Timestamp:</p>
              <p className="text-text-primary">{new Date(event.timestamp).toLocaleString()}</p>
            </div>
            <div className="mb-4">
              <p className="text-muted-foreground text-sm">Type:</p>
              <p className="text-text-primary">{event.type}</p>
            </div>
            <div className="mb-4">
              <p className="text-muted-foreground text-sm">Severity:</p>
              <p className={cn("font-bold", getSeverityColor(event.severity))}>{event.severity}</p>
            </div>
            <div className="mb-4">
              <p className="text-muted-foreground text-sm">Agent:</p>
              <p className="text-text-primary flex items-center"><Shield className="w-4 h-4 mr-2" />{event.agent}</p>
            </div>
            {event.sourceIp && (
              <div className="mb-4">
                <p className="text-muted-foreground text-sm">Source IP:</p>
                <p className="text-text-primary flex items-center"><Wifi className="w-4 h-4 mr-2" />{event.sourceIp}</p>
              </div>
            )}
            <div className="mb-4">
              <p className="text-muted-foreground text-sm">Message:</p>
              <p className="text-text-primary bg-background p-2 rounded-md border border-border">{event.message}</p>
            </div>
            {event.aiInsight && (
              <div className="mb-4 p-3 bg-accent/20 rounded-md border border-primary/50 text-primary">
                <p className="text-sm font-bold flex items-center"><Info className="w-4 h-4 mr-2" />AI INSIGHT:</p>
                <p className="text-sm">{event.aiInsight}</p>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-border flex justify-end">
            <Button onClick={onClose} variant="secondary">CLOSE</Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default EventDetailDrawer;
