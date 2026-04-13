import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ToggleLeft, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import StatusChip from '@/components/shared/StatusChip'; // Assuming StatusChip is in shared

const PluginCard = ({ plugin, onInspect, onToggleEnable }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.03, boxShadow: "0 0 20px rgba(0, 255, 138, 0.3)" }}
      transition={{ duration: 0.2 }}
    >
      <Card className="h-full flex flex-col justify-between">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-primary text-lg flex items-center">
              <ToggleLeft className="w-5 h-5 mr-2" />
              {plugin.name}
            </CardTitle>
            {plugin.signatureValid ? (
              <StatusChip status="healthy" className="bg-green-700/20 text-green-400">VALID</StatusChip>
            ) : (
              <StatusChip status="unhealthy" className="bg-red-700/20 text-destructive">INVALID</StatusChip>
            )}
          </div>
          <p className="text-sm text-text-secondary mt-2">{plugin.description}</p>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Version: {plugin.version}</span>
            <span>By: {plugin.author}</span>
          </div>
          <div className="flex gap-2 mt-auto">
            <Button
              onClick={() => onInspect(plugin)}
              variant="outline"
              className="flex-1 bg-background hover:bg-accent/20 text-text-primary border-border"
            >
              <Info className="w-4 h-4 mr-2" /> INSPECT
            </Button>
            <Button
              onClick={() => onToggleEnable(plugin.id, !plugin.enabled)}
              className={cn(
                "flex-1",
                plugin.enabled ? "bg-destructive hover:bg-destructive/90" : "bg-primary hover:bg-primary/90"
              )}
            >
              {plugin.enabled ? <XCircle className="w-4 h-4 mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              {plugin.enabled ? 'DISABLE' : 'ENABLE'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default PluginCard;
