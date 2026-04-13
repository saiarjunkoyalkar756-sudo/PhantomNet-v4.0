import React, { useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

const ThreatHuntingPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  const executeQuery = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // This is a placeholder for the actual API call
      // You will need to replace this with a call to your backend PNQL engine
      const response = await fetch('/api/pnql/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute query');
      }

      const data = await response.json();
      setResults(data.results.logs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader
        title="THREAT HUNTING"
        subtitle="Use PNQL to search for threats across all collected data."
      />

      <div className="p-4 bg-card rounded-lg shadow-sm">
        <div className="flex items-center space-x-2">
          <Textarea
            value={query}
            onChange={handleQueryChange}
            placeholder='e.g., SELECT * FROM logs WHERE event_type = "PROCESS_CREATE" AND details.name CONTAINS "powershell"'
            className="flex-1 font-mono"
            rows={3}
          />
          <Button onClick={executeQuery} disabled={isLoading}>
            <Search className="mr-2 h-4 w-4" />
            {isLoading ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0 mt-4">
        {error && (
          <div className="p-4 text-red-500 bg-red-100 rounded-lg">
            <strong>Error:</strong> {error}
          </div>
        )}
        <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Event Type</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.map((event) => (
                <TableRow key={event.id}>
                  <TableCell>{new Date(event.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{event.source}</TableCell>
                  <TableCell>{event.event_type}</TableCell>
                  <TableCell>
                    <pre className="text-xs bg-gray-100 p-2 rounded">
                      {JSON.stringify(event.details, null, 2)}
                    </pre>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </motion.div>
  );
};

export default ThreatHuntingPage;
