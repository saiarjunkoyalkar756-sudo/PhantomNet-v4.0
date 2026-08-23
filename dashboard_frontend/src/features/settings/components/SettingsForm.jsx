import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const SettingsForm = () => (
  <Card className="max-w-4xl mx-auto">
    <CardHeader><CardTitle className="text-xl text-primary">GOVERNED CONFIGURATION INTEGRATION PENDING</CardTitle></CardHeader>
    <CardContent className="space-y-4 text-sm text-text-secondary leading-6">
      <p>This dashboard cannot enable autonomous defense, alter threat scoring, change logging levels, or save system configuration. The prior local form implied operational settings changes without authenticated role scope, tenant boundaries, policy validation, change audit, review, or rollback.</p>
      <p>Any future configuration workflow must enforce privileged authorization and tenant scope, validate policy and safe defaults, record immutable auditable changes, require approval for high-impact settings, and preserve verification and rollback. AI remains advisory-only and cannot enable automated containment through this interface.</p>
    </CardContent>
  </Card>
);

export default SettingsForm;
