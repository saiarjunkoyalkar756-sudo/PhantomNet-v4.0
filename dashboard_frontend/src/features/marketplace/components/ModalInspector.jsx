import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { ToggleLeft, Info, FileText, CheckCircle, XCircle } from 'lucide-react';
import StatusChip from '@/components/shared/StatusChip';
import { Button } from '@/components/ui/Button';

const ModalInspector = ({ plugin, isOpen, onClose, onToggleEnable }) => {
  if (!plugin) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] bg-panel-solid border-border text-text-primary font-mono">
        <DialogHeader>
          <DialogTitle className="flex items-center text-primary text-xl">
            <ToggleLeft className="w-6 h-6 mr-2" />
            PLUGIN DETAILS: {plugin.name.toUpperCase()}
          </DialogTitle>
          <DialogDescription className="text-text-secondary text-sm">
            Detailed information and actions for <span className="text-primary">{plugin.name}</span>.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4 text-sm">
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">ID:</p>
            <p className="col-span-2 text-text-primary break-all">{plugin.id}</p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Status:</p>
            <div className="col-span-2">
                {plugin.enabled ? (
                    <StatusChip status="online" className="bg-primary/20 text-primary">ENABLED</StatusChip>
                ) : (
                    <StatusChip status="offline" className="bg-destructive/20 text-destructive">DISABLED</StatusChip>
                )}
            </div>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Version:</p>
            <p className="col-span-2 text-text-primary">{plugin.version}</p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Author:</p>
            <p className="col-span-2 text-text-primary">{plugin.author}</p>
          </div>
          <div className="grid grid-cols-3 items-center gap-4">
            <p className="text-muted-foreground">Signature:</p>
            <div className="col-span-2">
                {plugin.signatureValid ? (
                    <StatusChip status="healthy" className="bg-green-700/20 text-green-400">VALID</StatusChip>
                ) : (
                    <StatusChip status="unhealthy" className="bg-red-700/20 text-destructive">INVALID</StatusChip>
                )}
            </div>
          </div>
          <div className="grid grid-cols-3 items-start gap-4">
            <p className="text-muted-foreground">Description:</p>
            <p className="col-span-2 text-text-primary">{plugin.description}</p>
          </div>
          {plugin.configSchema && (
            <div>
              <p className="text-muted-foreground mb-2">Configuration Schema:</p>
              <pre className="bg-background border border-border p-2 rounded-md text-xs overflow-auto">
                {JSON.stringify(plugin.configSchema, null, 2)}
              </pre>
            </div>
          )}
        </div>
        <div className="flex justify-end space-x-2 border-t border-border pt-4 mt-4">
            <Button
                onClick={() => onToggleEnable(plugin.id, !plugin.enabled)}
                className={plugin.enabled ? "bg-destructive hover:bg-destructive/90" : "bg-primary hover:bg-primary/90"}
            >
                {plugin.enabled ? <XCircle className="w-4 h-4 mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                {plugin.enabled ? 'DISABLE' : 'ENABLE'}
            </Button>
            <Button variant="secondary" onClick={onClose}>CLOSE</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ModalInspector;
