import { motion } from 'framer-motion';
import React from 'react';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label'; // Assuming shadcn/ui label
// Placeholder for shadcn/ui label if not already generated
// In a real scenario, you would run `npx shadcn-ui add label`

const MotionDiv = motion.div;

const ToggleSwitch = ({ id, label, description, checked, onCheckedChange }) => {
  return (
    <MotionDiv
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-center justify-between p-4 bg-panel-solid/50 border border-border rounded-lg"
    >
      <div className="grid gap-1">
        <Label htmlFor={id} className="text-text-primary text-md font-medium">
          {label}
        </Label>
        {description && (
          <p className="text-sm text-text-secondary">
            {description}
          </p>
        )}
      </div>
      <Switch
        id={id}
        checked={checked}
        onCheckedChange={onCheckedChange}
      />
    </MotionDiv>
  );
};

export default ToggleSwitch;
