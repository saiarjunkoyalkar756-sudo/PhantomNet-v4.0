import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { FileText, Download, BarChart2, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'react-toastify';
import api from '../services/api';

const ComplianceReportingPage = () => {
  const [selectedStandard, setSelectedStandard] = useState('');
  const [generatedReports, setGeneratedReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get('/compliance-reporting/reports');
      setGeneratedReports(data || []);
    } catch (err) {
      console.error(`Error fetching reports: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    try {
      await api.post('/compliance-reporting/reports/generate', { standard: selectedStandard });
      toast.success(`${selectedStandard.toUpperCase()} report generated successfully!`);
      fetchReports();
    } catch (err) {
      toast.error(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleViewReportDetails = async (reportId) => {
    try {
      const data = await api.get(`/compliance-reporting/reports/${reportId}`);
      setSelectedReport(data);
    } catch (err) {
      toast.error(`Failed to load details: ${err.message}`);
    }
  };

  const handleDownloadPDF = (reportId) => {
    // Construct the download URL - standard practice is to use a direct link for binary downloads
    const downloadUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:3001/api'}/compliance-reporting/reports/${reportId}/download`;
    window.open(downloadUrl, '_blank');
    toast.info("Downloading compliance report...");
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="p-6 space-y-6"
    >
      <PageHeader
        title="Compliance & SOC2"
        subtitle="Automated audit evidence and regulatory reporting."
      />

      {error && (
        <div className="flex items-center p-4 text-red-800 bg-red-50 rounded-lg border border-red-200">
          <AlertCircle className="mr-2" />
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchReports} className="ml-auto">Retry</Button>
        </div>
      )}

      {/* Generator Card */}
      <div className="bg-card border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold mb-4 flex items-center">
          <FileText className="mr-2 text-primary" /> Generate Compliance Evidence
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="space-y-2">
            <Label>Standard</Label>
            <Select value={selectedStandard} onValueChange={setSelectedStandard}>
              <SelectTrigger>
                <SelectValue placeholder="Select Audit Standard" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="soc2">SOC2 Type II</SelectItem>
                <SelectItem value="iso27001">ISO 27001:2022</SelectItem>
                <SelectItem value="hipaa">HIPAA Compliance</SelectItem>
                <SelectItem value="pci-dss">PCI-DSS v4.0</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button 
            onClick={handleGenerateReport} 
            disabled={isGenerating || !selectedStandard}
            className="w-full md:w-auto"
          >
            {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Generate PDF Report
          </Button>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 bg-muted/50 border-b flex justify-between items-center">
          <h3 className="font-bold">Recent Reports</h3>
          <Button variant="ghost" size="sm" onClick={fetchReports}>Refresh</Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Standard</TableHead>
              <TableHead>Report ID</TableHead>
              <TableHead>Compliance Score</TableHead>
              <TableHead>Generated At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
                </TableCell>
              </TableRow>
            ) : generatedReports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                  No reports generated yet.
                </TableCell>
              </TableRow>
            ) : (
              generatedReports.map((report) => (
                <TableRow key={report.report_id}>
                  <TableCell className="font-medium text-primary">
                    {report.standard.toUpperCase()}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{report.report_id}</TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-1.5 mr-2">
                        <div 
                          className={`h-1.5 rounded-full ${report.score > 90 ? 'bg-green-500' : 'bg-yellow-500'}`} 
                          style={{ width: `${report.score}%` }}
                        />
                      </div>
                      <span className="text-sm font-bold">{report.score}%</span>
                    </div>
                  </TableCell>
                  <TableCell>{new Date(report.generated_at).toLocaleString()}</TableCell>
                  <TableCell className="text-right space-x-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => handleViewReportDetails(report.report_id)}>Details</Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Audit Findings: {report.standard.toUpperCase()}</DialogTitle>
                        </DialogHeader>
                        {selectedReport && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div className="p-3 bg-muted rounded-lg">
                                <Label className="text-xs text-muted-foreground">Report ID</Label>
                                <div className="font-mono">{selectedReport.report_id}</div>
                              </div>
                              <div className="p-3 bg-muted rounded-lg">
                                <Label className="text-xs text-muted-foreground">Score</Label>
                                <div className="font-bold text-lg">{selectedReport.details.compliance_score}%</div>
                              </div>
                            </div>
                            
                            <h4 className="font-bold text-sm">Security Controls Verified</h4>
                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                              {selectedReport.details.findings.map((finding, idx) => (
                                <div key={idx} className="p-3 border rounded-lg flex justify-between items-start gap-3">
                                  <div>
                                    <div className="font-bold text-xs">{finding.control_id}</div>
                                    <div className="text-xs text-muted-foreground">{finding.description}</div>
                                  </div>
                                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                                    finding.status === 'Compliant' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                  }`}>
                                    {finding.status}
                                  </span>
                                </div>
                              ))}
                            </div>
                            
                            <Button className="w-full" onClick={() => handleDownloadPDF(report.report_id)}>
                              <Download className="mr-2 h-4 w-4" /> Download PDF Artifact
                            </Button>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </motion.div>
  );
};

export default ComplianceReportingPage;
