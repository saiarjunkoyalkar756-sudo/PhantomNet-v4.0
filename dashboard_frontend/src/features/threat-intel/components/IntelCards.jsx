import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from '@/lib/utils';

const IntelCard = ({ title, value, icon: Icon, color = 'primary', children }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02, boxShadow: `0 0 15px rgba(var(--color-${color}-rgb), 0.5)` }}
      className="h-full"
    >
      <Card className="h-full">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-text-secondary">{title}</CardTitle>
          {Icon && <Icon className={cn("w-5 h-5", `text-${color}`)} />}
        </CardHeader>
        <CardContent>
          {value && <div className={cn("text-3xl font-bold", `text-${color}`)}>{value}</div>}
          {children}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default IntelCard;
