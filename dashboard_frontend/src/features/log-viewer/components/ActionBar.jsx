import React from 'react';
import { Button } from '@/components/ui/Button';
import { Copy, Download, RotateCcw } from 'lucide-react';
import { motion } from 'framer-motion';

const ActionBar = ({ onCopy, onExport, onClear }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-panel-solid backdrop-blur-md border border-border rounded-xl p-3 flex flex-wrap gap-3 justify-end"
    >
      <Button onClick={onCopy} variant="outline" className="text-primary hover:bg-accent/20 border-border">
        <Copy className="w-4 h-4 mr-2" /> COPY
      </Button>
      <Button onClick={onExport} variant="outline" className="text-primary hover:bg-accent/20 border-border">
        <Download className="w-4 h-4 mr-2" /> EXPORT
      </Button>
      <Button onClick={onClear} variant="destructive" className="hover:bg-destructive/90">
        <RotateCcw className="w-4 h-4 mr-2" /> CLEAR
      </Button>
    </motion.div>
  );
};

export default ActionBar;
