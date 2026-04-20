import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Users, PlusCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import AgentsTable from '@/features/agents/components/AgentsTable';

const AgentsManagementPage = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="AGENTS MANAGEMENT"
        subtitle="Manage and monitor your PhantomNet agent fleet."
        actions={
            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
                <PlusCircle className="w-4 h-4 mr-2" />ADD NEW AGENT
            </Button>
        }
      />
      
      <div className="flex-1 min-h-0">
        <AgentsTable />
      </div>
    </motion.div>
  );
};

export default AgentsManagementPage;
