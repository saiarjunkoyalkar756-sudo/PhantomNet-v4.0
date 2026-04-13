import React from 'react';
import { cn } from '@/lib/utils';

const PageHeader = ({ title, subtitle, actions, className }) => {
  return (
    <div className={cn('flex items-center justify-between mb-6', className)}>
      <div>
        <h1 className="text-3xl font-bold text-text-primary">{title}</h1>
        {subtitle && <p className="text-text-secondary mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center space-x-2">{actions}</div>}
    </div>
  );
};

export default PageHeader;
