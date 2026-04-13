import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const NetworkOverviewPage = () => {
  const [traffic, setTraffic] = useState(0);
  const [connections, setConnections] = useState(0);
  const [threats, setThreats] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/network`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'packet_metadata') {
        setTraffic(prevTraffic => prevTraffic + data.data.size);
      } else if (data.type === 'network_graph') {
        setConnections(data.data.connections.length);
      } else if (data.type.includes('anomaly')) {
        setThreats(prevThreats => prevThreats + 1);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="p-4 md:p-8">
      <h1 className="text-3xl font-bold mb-6">Network Overview</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Real-Time Traffic</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{(traffic / 1024).toFixed(2)} KB</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Active Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{connections}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Blocked Threats</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-red-500">{threats}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NetworkOverviewPage;
