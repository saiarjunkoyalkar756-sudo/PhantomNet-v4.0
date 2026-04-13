import React from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Settings, Sliders } from 'lucide-react';
import SettingsForm from '@/features/settings/components/SettingsForm';

const ConfigurationSettingsPage = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="CONFIGURATION & SETTINGS"
        subtitle="Manage PhantomNet system settings and preferences."
      />
      {/* Content for Configuration / Settings Page */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
        <SettingsForm />
      </div>
    </motion.div>
  );
};

export default ConfigurationSettingsPage;
