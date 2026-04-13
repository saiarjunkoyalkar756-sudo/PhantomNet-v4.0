import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { motion } from 'framer-motion';

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex w-full max-w-lg items-center space-x-2 bg-panel-solid/70 backdrop-blur-md border border-border rounded-lg p-2"
    >
      <input
        type="text"
        placeholder="Enter IP address, domain, or hash..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSearch();
          }
        }}
        className="flex-1 px-3 py-2 bg-transparent text-text-primary placeholder-text-secondary focus:outline-none"
      />
      <Button onClick={handleSearch} className="bg-primary hover:bg-primary/90 text-primary-foreground">
        <Search className="w-4 h-4 mr-2" />
        SEARCH
      </Button>
    </motion.div>
  );
};

export default SearchBar;
