import React from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

const StatusChip = ({ status, className }) => {
  let bgColor = "bg-gray-700";
  let textColor = "text-gray-200";
  let dotColor = "bg-gray-400";
  let animation = {};

  switch (status.toLowerCase()) {
    case 'online':
      bgColor = "bg-primary/20";
      textColor = "text-primary";
      dotColor = "bg-primary";
      animation = { scale: [1, 1.1, 1], transition: { duration: 1.5, repeat: Infinity } };
      break;
    case 'offline':
      bgColor = "bg-red-700/20";
      textColor = "text-destructive";
      dotColor = "bg-destructive";
      break;
    case 'quarantined':
      bgColor = "bg-yellow-700/20";
      textColor = "text-yellow-400";
      dotColor = "bg-yellow-400";
      animation = { opacity: [0.5, 1, 0.5], transition: { duration: 2, repeat: Infinity } };
      break;
    case 'healthy':
      bgColor = "bg-green-700/20";
      textColor = "text-green-400";
      dotColor = "bg-green-400";
      break;
    case 'unhealthy':
      bgColor = "bg-red-700/20";
      textColor = "text-destructive";
      dotColor = "bg-destructive";
      break;
    case 'pending':
      bgColor = "bg-blue-700/20";
      textColor = "text-blue-400";
      dotColor = "bg-blue-400";
      animation = { rotate: 360, transition: { duration: 2, repeat: Infinity, ease: "linear" } };
      break;
    default:
      break;
  }

  return (
    <motion.span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium",
        bgColor,
        textColor,
        className
      )}
    >
      <motion.span
        className={cn("w-2 h-2 rounded-full mr-1.5", dotColor)}
        animate={animation}
      ></motion.span>
      {status.toUpperCase()}
    </motion.span>
  );
};

export default StatusChip;
