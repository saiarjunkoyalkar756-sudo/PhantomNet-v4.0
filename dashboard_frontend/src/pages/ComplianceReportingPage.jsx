import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { FileText, Download, BarChart2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'react-toastify';

const ComplianceReportingPage = () => {
  const [selectedStandard, setSelectedStandard] = useState('');
  const [generatedReports, setGeneratedReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const commonHeaders = { 'Content-Type': 'application/json' };

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/compliance-reporting/reports');
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch reports');
      const data = await response.json();
      setGeneratedReports(data);
    } catch (err) {
      toast.error(`Error fetching reports: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/compliance-reporting/reports/generate', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify({ standard: selectedStandard }),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to generate report');
      toast.success('Report generated successfully!');
      fetchReports();
    } catch (err) {
      toast.error(`Error generating report: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewReportDetails = async (reportId) => {
    try {
      const response = await fetch(`/api/compliance-reporting/reports/${reportId}`);
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch report details');
      const data = await response.json();
      setSelectedReport(data);
    } catch (err) {
      toast.error(`Error fetching report details: ${err.message}`);
      setError(err.message);
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
        title="COMPLIANCE & REPORTING"
        subtitle="Generate automated compliance reports for various standards."
        actions={
          <div className="flex items-center space-x-2">
            <BarChart2 className="text-primary" size={20} />
          </div>
        }
      />

      {error && (
        <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="p-4 bg-card rounded-lg shadow-sm mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><FileText className="mr-2" /> Generate New Report</h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <Label htmlFor="complianceStandard">Compliance Standard</Label>
            <Select value={selectedStandard} onValueChange={setSelectedStandard}>
              <SelectTrigger id="complianceStandard">
                <SelectValue placeholder="Select Standard" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="iso27001">ISO 27001</SelectItem>
                <SelectItem value="soc2">SOC2</SelectItem>
                <SelectItem value="pci_dss">PCI-DSS</SelectItem>
                <SelectItem value="gdpr">GDPR</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleGenerateReport} disabled={isLoading || !selectedStandard} className="mt-7">
            Generate Report
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0 mt-4">
        <h3 className="text-lg font-semibold mb-2">Generated Reports</h3>
        <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Report ID</TableHead>
                <TableHead>Standard</TableHead>
                <TableHead>Generated At</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {generatedReports.map((report) => (
                <TableRow key={report.report_id}>
                  <TableCell>{report.report_id}</TableCell>
                  <TableCell>{report.standard}</TableCell>
                  <TableCell>{new Date(report.generated_at).toLocaleString()}</TableCell>
                  <TableCell>{report.status}</TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => handleViewReportDetails(report.report_id)}>View Details</Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[800px]">
                        <DialogHeader>
                          <DialogTitle>Report Details: {selectedReport?.report_id}</DialogTitle>
                        </DialogHeader>
                        {selectedReport && (
                          <div className="grid gap-4 py-4">
                            <p><strong>Standard:</strong> {selectedReport.standard}</p>
                            <p><strong>Generated At:</strong> {new Date(selectedReport.generated_at).toLocaleString()}</p>
                            <p><strong>Status:</strong> {selectedReport.status}</p>
                            <p><strong>Summary:</strong> {selectedReport.summary}</p>
                            <h4 className="font-semibold mt-2">Findings</h4>
                            {selectedReport.details?.findings && selectedReport.details.findings.length > 0 ? (
                                <ul className="list-disc pl-5">
                                    {selectedReport.details.findings.map((finding, idx) => (
                                        <li key={idx}>
                                            <strong>{finding.control_id} ({finding.status}):</strong> {finding.description} (Severity: {finding.severity || 'N/A'})
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>No specific findings reported.</p>
                            )}
                            <h4 className="font-semibold mt-2">Recommendations</h4>
                            {selectedReport.details?.recommendations && selectedReport.details.recommendations.length > 0 ? (
                                <ul className="list-disc pl-5">
                                    {selectedReport.details.recommendations.map((rec, idx) => (
                                        <li key={idx}>{rec}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p>No specific recommendations.</p>
                            )}
                            <Button className="mt-4" onClick={() => toast.info("Download simulated!")}>
                              <Download className="mr-2 h-4 w-4" /> Download Report (Simulated)
                            </Button>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
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

export default ComplianceReportingPage;
