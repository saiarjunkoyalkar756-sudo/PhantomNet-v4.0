import { motion } from 'framer-motion';
import React from 'react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Terminal, Code } from 'lucide-react';
const MotionDiv = motion.div;

const FormatSwitch = ({ format, onFormatChange }) => {
  return (
    <MotionDiv initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
      <ToggleGroup type="single" value={format} onValueChange={onFormatChange} aria-label="Log format selection">
        <ToggleGroupItem value="raw" aria-label="Toggle raw format" className="font-mono text-xs">
          <Terminal className="h-4 w-4 mr-2" /> RAW
        </ToggleGroupItem>
        <ToggleGroupItem value="formatted" aria-label="Toggle formatted format" className="font-mono text-xs">
          <Code className="h-4 w-4 mr-2" /> FORMATTED
        </ToggleGroupItem>
      </ToggleGroup>
    </MotionDiv>
  );
};

export default FormatSwitch;
