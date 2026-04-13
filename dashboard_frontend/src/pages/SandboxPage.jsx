import React, { useState } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Upload, Play, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'react-toastify';

const SandboxPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setAnalysisResult(null); // Clear previous results
    setError(null);
  };

  const handleAnalyzeFile = async () => {
    if (!selectedFile) {
      toast.error('Please select a file to analyze.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/sandbox/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'File analysis failed');
      }

      const data = await response.json();
      setAnalysisResult(data);
      toast.success('File analysis completed!');
    } catch (err) {
      toast.error(`Error analyzing file: ${err.message}`);
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
        title="MALWARE SANDBOX"
        subtitle="Submit suspicious files for automated analysis in a virtualized environment."
        actions={
          <div className="flex items-center space-x-2">
            <Play className="text-primary" size={20} />
          </div>
        }
      />

      <div className="p-4 bg-card rounded-lg shadow-sm mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><Upload className="mr-2" /> Upload File for Analysis</h3>
        <div className="flex items-center space-x-4">
          <Input type="file" onChange={handleFileChange} className="flex-1" />
          <Button onClick={handleAnalyzeFile} disabled={isLoading || !selectedFile}>
            {isLoading ? 'Analyzing...' : 'Analyze File'}
          </Button>
        </div>
        {selectedFile && (
          <p className="text-sm text-muted-foreground mt-2">Selected: {selectedFile.name}</p>
        )}
      </div>

      {error && (
        <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      {analysisResult && (
        <div className="flex-1 min-h-0 mt-4">
          <h3 className="text-lg font-semibold mb-2">Analysis Results for {analysisResult.file_name}</h3>
          <div className="bg-card rounded-lg shadow-sm p-4 mb-4">
            <div className="flex items-center space-x-2 text-lg font-bold">
              Verdict: {analysisResult.verdict === 'MALICIOUS' ? (
                <span className="text-red-500 flex items-center"><XCircle className="mr-1" /> MALICIOUS</span>
              ) : analysisResult.verdict === 'CLEAN' ? (
                <span className="text-green-500 flex items-center"><CheckCircle className="mr-1" /> CLEAN</span>
              ) : (
                <span className="text-yellow-500 flex items-center"><ShieldAlert className="mr-1" /> SUSPICIOUS</span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">File Hash (SHA256): {analysisResult.file_hash}</p>
            <p className="text-sm text-muted-foreground">Analysis ID: {analysisResult.analysis_id}</p>
          </div>

          <Tabs defaultValue="api_behaviors" className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="api_behaviors">API Behaviors</TabsTrigger>
              <TabsTrigger value="network_traffic">Network Traffic</TabsTrigger>
              <TabsTrigger value="crypto_routines">Crypto Routines</TabsTrigger>
              <TabsTrigger value="dropped_artifacts">Dropped Artifacts</TabsTrigger>
            </TabsList>
            <TabsContent value="api_behaviors" className="flex-1 min-h-0 p-0">
              <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Behavior</TableHead>
                      <TableHead>Count</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(analysisResult.api_behaviors).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>{key.replace(/_/g, ' ')}</TableCell>
                        <TableCell>{value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
            <TabsContent value="network_traffic" className="flex-1 min-h-0 p-0">
              <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(analysisResult.network_traffic).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>{key.replace(/_/g, ' ')}</TableCell>
                        <TableCell>{Array.isArray(value) ? value.join(', ') : value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
            <TabsContent value="crypto_routines" className="flex-1 min-h-0 p-0">
              <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Routine</TableHead>
                      <TableHead>Detected</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(analysisResult.crypto_routines).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>{key.replace(/_/g, ' ')}</TableCell>
                        <TableCell>{value ? 'Yes' : 'No'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
            <TabsContent value="dropped_artifacts" className="flex-1 min-h-0 p-0">
              <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Artifacts</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(analysisResult.dropped_artifacts).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>{key.replace(/_/g, ' ')}</TableCell>
                        <TableCell>{Array.isArray(value) ? value.join(', ') : value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
          </Tabs>

          <div className="bg-card rounded-lg shadow-sm p-4 mt-4">
            <h4 className="text-md font-semibold mb-2">Raw Analysis Output</h4>
            <pre className="text-sm bg-gray-100 p-2 rounded max-h-40 overflow-y-auto">
              {analysisResult.raw_output}
            </pre>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default SandboxPage;
