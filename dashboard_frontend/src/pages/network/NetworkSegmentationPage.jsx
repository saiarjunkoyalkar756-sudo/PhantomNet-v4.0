import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import NetworkGraph from '@/components/network/NetworkGraph';

const NetworkSegmentationPage = () => {
  const [segments, setSegments] = useState([]);
  const [violations, setViolations] = useState([]);

  useEffect(() => {
    fetch('/api/v1/network/segmentation')
      .then(response => response.json())
      .then(data => setSegments(data));

    fetch('/api/v1/network/violations')
      .then(response => response.json())
      .then(data => setViolations(data));
  }, []);

  return (
    <div className="p-4 md:p-8">
      <h1 className="text-3xl font-bold mb-6">Network Segmentation</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Segmentation Map</CardTitle>
          </CardHeader>
          <CardContent>
            <NetworkGraph />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Segmentation Violations</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  <TableHead>Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {violations.map((violation) => (
                  <TableRow key={violation.id}>
                    <TableCell>{violation.source_ip}</TableCell>
                    <TableCell>{violation.destination_ip}</TableCell>
                    <TableCell>{violation.timestamp}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NetworkSegmentationPage;
