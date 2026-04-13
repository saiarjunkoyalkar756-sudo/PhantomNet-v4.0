import React, { useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Globe, Search, AlertTriangle, ListFilter } from 'lucide-react';
import SearchBar from '@/features/threat-intel/components/SearchBar';
import IntelCard from '@/features/threat-intel/components/IntelCards';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ThreatIntelOSINTPage = () => {
  const [ipQueryResult, setIpQueryResult] = useState(null);

  const handleIpSearch = (query) => {
    console.log("Searching for:", query);
    // Simulate API call
    setTimeout(() => {
      setIpQueryResult({
        ip: query,
        reputation: Math.floor(Math.random() * 100),
        country: 'USA',
        city: 'New York',
        isp: 'Example ISP',
        maliciousReports: Math.floor(Math.random() * 50),
      });
    }, 1000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="THREAT INTEL OSINT HUB"
        subtitle="Open-Source Intelligence and Threat Data Aggregation."
      />
      
      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        {/* Left Column - IP Lookup & GeoIP */}
        <div className="flex-1 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-primary">
                <Search className="w-5 h-5 mr-2" />
                IP / DOMAIN LOOKUP
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <SearchBar onSearch={handleIpSearch} />
              {ipQueryResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="mt-6 w-full grid grid-cols-1 md:grid-cols-2 gap-4"
                >
                  <IntelCard title="Reputation Score" value={`${ipQueryResult.reputation}/100`} color={ipQueryResult.reputation < 50 ? 'destructive' : 'primary'} />
                  <IntelCard title="Malicious Reports" value={ipQueryResult.maliciousReports} color={ipQueryResult.maliciousReports > 0 ? 'destructive' : 'primary'} />
                  <IntelCard title="Country" value={ipQueryResult.country} icon={Globe} />
                  <IntelCard title="ISP" value={ipQueryResult.isp} />
                </motion.div>
              )}
            </CardContent>
          </Card>
          
          <Card className="flex-1">
            <CardHeader>
              <CardTitle className="flex items-center text-primary">
                <Globe className="w-5 h-5 mr-2" />
                GEOIP LOCATION
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex items-center justify-center">
              <p className="text-text-secondary">GeoIP map visualization here...</p>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - IOC List & OSINT Evidence */}
        <div className="flex-1 flex flex-col gap-6">
          <Card className="flex-1">
            <CardHeader>
              <CardTitle className="flex items-center text-primary">
                <AlertTriangle className="w-5 h-5 mr-2" />
                IOC LIST VIEWER
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex items-center justify-center">
              <p className="text-text-secondary">Indicators of Compromise list will go here...</p>
            </CardContent>
          </Card>

          <Card className="flex-1">
            <CardHeader>
              <CardTitle className="flex items-center text-primary">
                <ListFilter className="w-5 h-5 mr-2" />
                OSINT EVIDENCE TIMELINE
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex items-center justify-center">
              <p className="text-text-secondary">Timeline of OSINT findings...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default ThreatIntelOSINTPage;
