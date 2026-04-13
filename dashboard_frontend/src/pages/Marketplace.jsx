import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Puzzle, Store } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import MarketplaceGrid from '@/features/marketplace/components/MarketplaceGrid';

const Marketplace = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="PLUGIN & AI MARKETPLACE"
        subtitle="Discover and manage powerful extensions and AI personalities for PhantomNet."
        actions={
            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
                <Store className="w-4 h-4 mr-2" />BROWSE CATEGORIES
            </Button>
        }
      />
      {/* Content for Marketplace */}
      <div className="flex-1 min-h-0">
        <MarketplaceGrid />
      </div>
    </motion.div>
  );
};

export default Marketplace;
