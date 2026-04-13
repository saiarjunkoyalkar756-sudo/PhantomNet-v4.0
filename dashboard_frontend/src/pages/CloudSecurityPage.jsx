import React, { useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Cloud, Lock, ShieldAlert, Aws } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';

const CloudSecurityPage = () => {
  const [awsAccessKeyId, setAwsAccessKeyId] = useState('');
  const [awsSecretAccessKey, setAwsSecretAccessKey] = useState('');
  const [awsRegion, setAwsRegion] = useState('us-east-1');
  const [awsResourceId, setAwsResourceId] = useState('');
  const [misconfigurations, setMisconfigurations] = useState([]);
  const [iamAlerts, setIamAlerts] = useState([]);
  const [s3Exposure, setS3Exposure] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const commonHeaders = { 'Content-Type': 'application/json' };

  const buildAwsPayload = () => ({
    aws_access_key_id: awsAccessKeyId,
    aws_secret_access_key: awsSecretAccessKey,
    region_name: awsRegion,
    resource_id: awsResourceId || undefined,
  });

  const handleAwsMisconfiguration = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/cloud-security/aws/misconfiguration', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify(buildAwsPayload()),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'AWS Misconfiguration check failed');
      const data = await response.json();
      setMisconfigurations(data.misconfigurations);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleIamAbuseDetection = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/cloud-security/aws/iam_abuse', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify(buildAwsPayload()),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'IAM Abuse detection failed');
      const data = await response.json();
      setIamAlerts(data.alerts);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleS3ExposureAlerts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/cloud-security/aws/s3_exposure', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify(buildAwsPayload()),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'S3 Exposure check failed');
      const data = await response.json();
      setS3Exposure(data.exposed_buckets);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const isAwsConfigValid = awsAccessKeyId && awsSecretAccessKey && awsRegion;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader
        title="CLOUD SECURITY"
        subtitle="Monitor and secure your cloud environments (AWS, Azure, GCP)."
        actions={
          <div className="flex items-center space-x-2">
            <Cloud className="text-primary" size={20} />
          </div>
        }
      />

      <div className="p-4 bg-card rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><Aws className="mr-2" />AWS Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <Label htmlFor="awsAccessKeyId">AWS Access Key ID</Label>
            <Input id="awsAccessKeyId" type="password" value={awsAccessKeyId} onChange={(e) => setAwsAccessKeyId(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="awsSecretAccessKey">AWS Secret Access Key</Label>
            <Input id="awsSecretAccessKey" type="password" value={awsSecretAccessKey} onChange={(e) => setAwsSecretAccessKey(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="awsRegion">AWS Region</Label>
            <Input id="awsRegion" value={awsRegion} onChange={(e) => setAwsRegion(e.target.value)} placeholder="e.g., us-east-1" />
          </div>
          <div>
            <Label htmlFor="awsResourceId">AWS Resource ID (Optional)</Label>
            <Input id="awsResourceId" value={awsResourceId} onChange={(e) => setAwsResourceId(e.target.value)} placeholder="e.g., my-s3-bucket" />
          </div>
        </div>
        <div className="flex space-x-4">
          <Button onClick={handleAwsMisconfiguration} disabled={isLoading || !isAwsConfigValid}>
            <Lock className="mr-2 h-4 w-4" /> Check Misconfigurations
          </Button>
          <Button onClick={handleIamAbuseDetection} disabled={isLoading || !isAwsConfigValid}>
            <ShieldAlert className="mr-2 h-4 w-4" /> Detect IAM Abuse
          </Button>
          <Button onClick={handleS3ExposureAlerts} disabled={isLoading || !isAwsConfigValid}>
            <Cloud className="mr-2 h-4 w-4" /> S3 Exposure Alerts
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0 mt-4">
        {error && (
          <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        <Tabs defaultValue="misconfigurations" className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="misconfigurations">Misconfigurations</TabsTrigger>
            <TabsTrigger value="iam_abuse">IAM Abuse Alerts</TabsTrigger>
            <TabsTrigger value="s3_exposure">S3 Exposure</TabsTrigger>
          </TabsList>
          <TabsContent value="misconfigurations" className="flex-1 min-h-0 p-0">
            <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {misconfigurations.map((alert, index) => (
                    <TableRow key={index}>
                      <TableCell>{alert.type}</TableCell>
                      <TableCell>{alert.resource}</TableCell>
                      <TableCell>{alert.severity}</TableCell>
                      <TableCell>{alert.details}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
          <TabsContent value="iam_abuse" className="flex-1 min-h-0 p-0">
            <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {iamAlerts.map((alert, index) => (
                    <TableRow key={index}>
                      <TableCell>{alert.type}</TableCell>
                      <TableCell>{alert.resource}</TableCell>
                      <TableCell>{alert.severity}</TableCell>
                      <TableCell>{alert.details}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
          <TabsContent value="s3_exposure" className="flex-1 min-h-0 p-0">
            <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {s3Exposure.map((alert, index) => (
                    <TableRow key={index}>
                      <TableCell>{alert.type}</TableCell>
                      <TableCell>{alert.resource}</TableCell>
                      <TableCell>{alert.severity}</TableCell>
                      <TableCell>{alert.details}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
};

export default CloudSecurityPage;
