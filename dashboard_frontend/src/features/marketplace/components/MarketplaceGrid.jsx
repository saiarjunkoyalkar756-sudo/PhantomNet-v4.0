import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PluginCard from './PluginCard';
import ModalInspector from './ModalInspector';

// Dummy data for plugins
const initialPlugins = [
  {
    id: 'plugin-xdr',
    name: 'Advanced XDR Integration',
    description: 'Integrates with leading XDR platforms for enhanced threat detection and response.',
    version: '1.0.0',
    author: 'PhantomNet Labs',
    enabled: true,
    signatureValid: true,
    configSchema: { endpoint: 'url', apiKey: 'string' }
  },
  {
    id: 'plugin-honeypot',
    name: 'Decoy Honeypot Network',
    description: 'Deploys a network of decoy systems to trap and analyze attacker behavior.',
    version: '1.2.0',
    author: 'Cyber-Dynamics Inc.',
    enabled: false,
    signatureValid: true,
    configSchema: { network: 'cidr', type: 'string' }
  },
  {
    id: 'plugin-ai-hunter',
    name: 'AI Threat Hunter',
    description: 'Utilizes AI to proactively hunt for emerging threats and anomalies across your infrastructure.',
    version: '1.1.0',
    author: 'PhantomNet AI',
    enabled: true,
    signatureValid: false, // Example of invalid signature
    configSchema: { sensitivity: 'number', frequency: 'string' }
  },
  {
    id: 'plugin-blockchain',
    name: 'Blockchain Traceability Module',
    description: 'Provides immutable logging and traceability of security events using distributed ledger technology.',
    version: '1.0.5',
    author: 'Decentralized Security Co.',
    enabled: false,
    signatureValid: true,
    configSchema: { chain: 'string', wallet: 'address' }
  },
];

const MarketplaceGrid = () => {
  const [plugins, setPlugins] = useState(initialPlugins);
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  const handleInspect = (plugin) => {
    setSelectedPlugin(plugin);
    setModalOpen(true);
  };

  const handleToggleEnable = (id, enabled) => {
    setPlugins(prevPlugins =>
      prevPlugins.map(plugin =>
        plugin.id === id ? { ...plugin, enabled: enabled } : plugin
      )
    );
    // If the inspected plugin is the one being toggled, update its state too
    if (selectedPlugin && selectedPlugin.id === id) {
        setSelectedPlugin(prev => ({ ...prev, enabled: enabled }));
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <AnimatePresence>
        {plugins.map((plugin) => (
          <PluginCard
            key={plugin.id}
            plugin={plugin}
            onInspect={handleInspect}
            onToggleEnable={handleToggleEnable}
          />
        ))}
      </AnimatePresence>

      <ModalInspector
        plugin={selectedPlugin}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onToggleEnable={handleToggleEnable}
      />
    </motion.div>
  );
};

export default MarketplaceGrid;
