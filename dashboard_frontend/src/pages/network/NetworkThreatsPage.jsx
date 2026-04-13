import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const NetworkThreatsPage = () => {
  const [threats, setThreats] = useState([]);

  useEffect(() => {
    fetch('/api/v1/network/threats')
      .then(response => response.json())
      .then(data => setThreats(data));
  }, []);

  return (
    <div className="p-4 md:p-8">
      <h1 className="text-3xl font-bold mb-6">Network Threats</h1>
      <Card>
        <CardHeader>
          <CardTitle>Recent Threats</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Source IP</TableHead>
                <TableHead>Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {threats.map((threat) => (
                <TableRow key={threat.id}>
                  <TableCell className="font-medium text-red-500">{threat.type}</TableCell>
                  <TableCell>{threat.source}</TableCell>
                  <TableCell>{threat.timestamp}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default NetworkThreatsPage;
