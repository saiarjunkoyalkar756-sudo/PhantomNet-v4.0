import React, { useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Network } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

const GraphInvestigationPage = () => {
  const [cypherQuery, setCypherQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQueryChange = (event) => {
    setCypherQuery(event.target.value);
  };

  const executeQuery = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/graph-intelligence/graph', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: cypherQuery }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute query');
      }

      const data = await response.json();
      setResults(data.results || []);
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
        title="GRAPH INVESTIGATION"
        subtitle="Explore relationships between entities using Cypher queries."
        actions={
            <div className="flex items-center space-x-2">
                <Network className="text-primary" size={20} />
            </div>
        }
      />

      <div className="p-4 bg-card rounded-lg shadow-sm">
        <div className="flex items-center space-x-2">
          <Textarea
            value={cypherQuery}
            onChange={handleQueryChange}
            placeholder='e.g., MATCH (p:Process)-[:OPENED]->(f:File) RETURN p.name, f.name LIMIT 10'
            className="flex-1 font-mono"
            rows={3}
          />
          <Button onClick={executeQuery} disabled={isLoading}>
            {isLoading ? 'Executing...' : 'Execute Cypher'}
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
                {results.length > 0 &&
                  Object.keys(results[0]).map((key) => (
                    <TableHead key={key}>{key}</TableHead>
                  ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.map((row, index) => (
                <TableRow key={index}>
                  {Object.values(row).map((value, idx) => (
                    <TableCell key={idx}>
                      {typeof value === 'object' ? JSON.stringify(value) : value}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </motion.div>
  );
};

export default GraphInvestigationPage;
