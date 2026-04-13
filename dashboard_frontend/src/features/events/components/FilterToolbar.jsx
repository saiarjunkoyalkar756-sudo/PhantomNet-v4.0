import React from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Filter, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

const FilterToolbar = ({ isPaused, togglePause, filters, setFilters }) => {

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value,
    }));
  };

  const clearFilter = (filterType) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: '',
    }));
  };

  const filterOptions = {
    severity: ['High', 'Medium', 'Low', 'Informational', ''], // Empty for 'All'
    type: ['Threat Detected', 'Anomaly Alert', 'Agent Offline', 'Policy Violation', ''],
    agent: ['agent-alpha-1', 'agent-beta-2', 'agent-gamma-3', 'agent-delta-4', ''],
  };

  const selectClasses = "bg-background border border-border rounded-md text-text-primary text-sm p-2 focus:ring-primary focus:border-primary";
  const labelClasses = "text-text-secondary text-sm mr-2";


  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-panel-solid backdrop-blur-md border border-border rounded-xl p-4 mb-4 flex flex-wrap items-center gap-4"
    >
      <div className="flex items-center gap-2">
        <Button
          onClick={togglePause}
          className={cn("text-primary-foreground", isPaused ? "bg-primary hover:bg-primary/90" : "bg-destructive hover:bg-destructive/90")}
        >
          {isPaused ? <Play className="w-4 h-4 mr-2" /> : <Pause className="w-4 h-4 mr-2" />}
          {isPaused ? 'RESUME STREAM' : 'PAUSE STREAM'}
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Filter className="text-text-secondary" size={18} />
        <span className="text-text-secondary text-sm">FILTERS:</span>
      </div>

      {/* Severity Filter */}
      <div className="flex items-center">
        <label htmlFor="severity-filter" className={labelClasses}>Severity:</label>
        <select
          id="severity-filter"
          value={filters.severity}
          onChange={(e) => handleFilterChange('severity', e.target.value)}
          className={selectClasses}
        >
          <option value="">ALL</option>
          {filterOptions.severity.map(opt => opt && <option key={opt} value={opt}>{opt.toUpperCase()}</option>)}
        </select>
        {filters.severity && (
          <Button variant="ghost" size="icon" onClick={() => clearFilter('severity')} className="ml-1">
            <XCircle size={16} className="text-destructive" />
          </Button>
        )}
      </div>

      {/* Type Filter */}
      <div className="flex items-center">
        <label htmlFor="type-filter" className={labelClasses}>Type:</label>
        <select
          id="type-filter"
          value={filters.type}
          onChange={(e) => handleFilterChange('type', e.target.value)}
          className={selectClasses}
        >
          <option value="">ALL</option>
          {filterOptions.type.map(opt => opt && <option key={opt} value={opt}>{opt.toUpperCase()}</option>)}
        </select>
        {filters.type && (
          <Button variant="ghost" size="icon" onClick={() => clearFilter('type')} className="ml-1">
            <XCircle size={16} className="text-destructive" />
          </Button>
        )}
      </div>

      {/* Agent Filter */}
      <div className="flex items-center">
        <label htmlFor="agent-filter" className={labelClasses}>Agent:</label>
        <select
          id="agent-filter"
          value={filters.agent}
          onChange={(e) => handleFilterChange('agent', e.target.value)}
          className={selectClasses}
        >
          <option value="">ALL</option>
          {filterOptions.agent.map(opt => opt && <option key={opt} value={opt}>{opt.toUpperCase()}</option>)}
        </select>
        {filters.agent && (
          <Button variant="ghost" size="icon" onClick={() => clearFilter('agent')} className="ml-1">
            <XCircle size={16} className="text-destructive" />
          </Button>
        )}
      </div>

    </motion.div>
  );
};

export default FilterToolbar;
