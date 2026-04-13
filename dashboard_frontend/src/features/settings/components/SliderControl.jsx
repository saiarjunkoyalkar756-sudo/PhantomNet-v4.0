import React from 'react';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { motion } from 'framer-motion';

const SliderControl = ({ id, label, description, value, onValueChange, min, max, step }) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-2 p-4 bg-panel-solid/50 border border-border rounded-lg"
    >
      <div className="flex justify-between items-center">
        <Label htmlFor={id} className="text-text-primary text-md font-medium">
          {label}
        </Label>
        <span className="text-primary font-mono text-lg">{value}</span>
      </div>
      {description && (
        <p className="text-sm text-text-secondary">
          {description}
        </p>
      )}
      <Slider
        id={id}
        min={min}
        max={max}
        step={step}
        value={[value]}
        onValueChange={(val) => onValueChange(val[0])}
        className="w-full"
      />
    </motion.div>
  );
};

export default SliderControl;
