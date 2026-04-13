import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Plug, PlusCircle, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'react-toastify';

const SiemIntegrationPage = () => {
  const [siemType, setSiemType] = useState('');
  const [connectionName, setConnectionName] = useState('');
  const [configJson, setConfigJson] = useState('{}');
  const [connections, setConnections] = useState([]);
  const [selectedSiemForEvent, setSelectedSiemForEvent] = useState('');
  const [testEventData, setTestEventData] = useState('{"message": "Test event from PhantomNet"}');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const commonHeaders = { 'Content-Type': 'application/json' };

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await fetch('/api/siem-integration/connections');
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch connections');
      const data = await response.json();
      setConnections(data.connections);
    } catch (err) {
      toast.error(`Error fetching connections: ${err.message}`);
      setError(err.message);
    }
  };

  const handleAddConnection = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = {
        siem_type: siemType,
        name: connectionName,
        config: JSON.parse(configJson),
      };
      const response = await fetch('/api/siem-integration/connections', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to add connection');
      toast.success('Connection added successfully!');
      setSiemType('');
      setConnectionName('');
      setConfigJson('{}');
      fetchConnections();
    } catch (err) {
      toast.error(`Error adding connection: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendTestEvent = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = {
        siem_name: selectedSiemForEvent,
        event_data: JSON.parse(testEventData),
      };
      const response = await fetch('/api/siem-integration/send_event', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to send test event');
      toast.success('Test event sent successfully!');
    } catch (err) {
      toast.error(`Error sending test event: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const isAddConnectionValid = siemType && connectionName && configJson;
  const isSendEventValid = selectedSiemForEvent && testEventData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader
        title="SIEM INTEGRATION"
        subtitle="Connect PhantomNet with your existing SIEM solutions."
        actions={
          <div className="flex items-center space-x-2">
            <Plug className="text-primary" size={20} />
          </div>
        }
      />

      <div className="p-4 bg-card rounded-lg shadow-sm mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><PlusCircle className="mr-2" /> Add New SIEM Connection</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <Label htmlFor="siemType">SIEM Type</Label>
            <Select value={siemType} onValueChange={setSiemType}>
              <SelectTrigger id="siemType">
                <SelectValue placeholder="Select SIEM Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="splunk">Splunk</SelectItem>
                <SelectItem value="elk">ELK Stack</SelectItem>
                <SelectItem value="wazuh">Wazuh</SelectItem>
                <SelectItem value="qradar">QRadar</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="connectionName">Connection Name</Label>
            <Input id="connectionName" value={connectionName} onChange={(e) => setConnectionName(e.target.value)} placeholder="e.g., MySplunkInstance" />
          </div>
        </div>
        <div>
          <Label htmlFor="configJson">Configuration (JSON)</Label>
          <Textarea id="configJson" value={configJson} onChange={(e) => setConfigJson(e.target.value)} rows={5} className="font-mono" />
        </div>
        <Button onClick={handleAddConnection} disabled={isLoading || !isAddConnectionValid} className="mt-4">
          Add Connection
        </Button>
      </div>

      <div className="p-4 bg-card rounded-lg shadow-sm mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><Send className="mr-2" /> Send Test Event</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <Label htmlFor="selectedSiemForEvent">Select SIEM Connection</Label>
            <Select value={selectedSiemForEvent} onValueChange={setSelectedSiemForEvent}>
              <SelectTrigger id="selectedSiemForEvent">
                <SelectValue placeholder="Select a SIEM" />
              </SelectTrigger>
              <SelectContent>
                {connections.map((conn) => (
                  <SelectItem key={conn.name} value={conn.name}>
                    {conn.name} ({conn.siem_type})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div /> {/* Empty div for layout */}
        </div>
        <div>
          <Label htmlFor="testEventData">Test Event Data (JSON)</Label>
          <Textarea id="testEventData" value={testEventData} onChange={(e) => setTestEventData(e.target.value)} rows={5} className="font-mono" />
        </div>
        <Button onClick={handleSendTestEvent} disabled={isLoading || !isSendEventValid} className="mt-4">
          Send Test Event
        </Button>
      </div>

      <div className="flex-1 min-h-0 mt-4">
        {error && (
          <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}
        <h3 className="text-lg font-semibold mb-2">Existing SIEM Connections</h3>
        <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Config</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {connections.map((conn) => (
                <TableRow key={conn.name}>
                  <TableCell>{conn.name}</TableCell>
                  <TableCell>{conn.siem_type}</TableCell>
                  <TableCell>
                    <pre className="text-xs bg-gray-100 p-2 rounded">
                      {JSON.stringify(conn.config, null, 2)}
                    </pre>
                  </TableCell>
                  <TableCell>
                    {/* Add edit/delete buttons here */}
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

export default SiemIntegrationPage;
