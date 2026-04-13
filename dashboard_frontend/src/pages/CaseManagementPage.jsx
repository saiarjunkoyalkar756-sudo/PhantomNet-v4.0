import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Briefcase, PlusCircle, FileText, User, Play, Edit } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'react-toastify';

const CaseManagementPage = () => {
  const [cases, setCases] = useState([]);
  const [newCase, setNewCase] = useState({ title: '', description: '', severity: 'medium', assigned_to: '' });
  const [selectedCase, setSelectedCase] = useState(null);
  const [noteContent, setNoteContent] = useState('');
  const [updateStatus, setUpdateStatus] = useState('');
  const [updateAssignee, setUpdateAssignee] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const commonHeaders = { 'Content-Type': 'application/json' };

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/case-management/cases');
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch cases');
      const data = await response.json();
      setCases(data);
    } catch (err) {
      toast.error(`Error fetching cases: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateCase = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/case-management/cases', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify(newCase),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to create case');
      toast.success('Case created successfully!');
      setNewCase({ title: '', description: '', severity: 'medium', assigned_to: '' });
      fetchCases();
    } catch (err) {
      toast.error(`Error creating case: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateCase = async (caseId, updates) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/case-management/cases/${caseId}`, {
        method: 'PUT',
        headers: commonHeaders,
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to update case');
      toast.success('Case updated successfully!');
      fetchCases();
      if (selectedCase && selectedCase.id === caseId) {
        setSelectedCase(prev => ({ ...prev, ...updates }));
      }
    } catch (err) {
      toast.error(`Error updating case: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddNote = async (caseId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/case-management/cases/${caseId}/add_note`, {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify({ note: noteContent }),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to add note');
      toast.success('Note added successfully!');
      setNoteContent('');
      fetchCases();
      if (selectedCase && selectedCase.id === caseId) {
        setSelectedCase(prev => ({ ...prev, notes: [...prev.notes, { timestamp: new Date().toISOString(), note: noteContent }] }));
      }
    } catch (err) {
      toast.error(`Error adding note: ${err.message}`);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecutePlaybook = async (caseId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/case-management/cases/${caseId}/execute_playbook`, {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify({ playbook_name: 'default_playbook' }), // Hardcoded for now
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to execute playbook');
      toast.success('Playbook executed successfully!');
      fetchCases();
    } catch (err) {
      toast.error(`Error executing playbook: ${err.message}`);
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
        title="INCIDENT CASE MANAGEMENT"
        subtitle="Manage security incidents from detection to resolution."
        actions={
          <div className="flex items-center space-x-2">
            <Briefcase className="text-primary" size={20} />
          </div>
        }
      />

      {error && (
        <div className="p-4 text-red-500 bg-red-100 rounded-lg mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="p-4 bg-card rounded-lg shadow-sm mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center"><PlusCircle className="mr-2" /> Create New Case</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <Label htmlFor="caseTitle">Title</Label>
            <Input id="caseTitle" value={newCase.title} onChange={(e) => setNewCase({ ...newCase, title: e.target.value })} placeholder="e.g., Suspicious Login Attempt" />
          </div>
          <div>
            <Label htmlFor="caseSeverity">Severity</Label>
            <Select value={newCase.severity} onValueChange={(value) => setNewCase({ ...newCase, severity: value })}>
              <SelectTrigger id="caseSeverity">
                <SelectValue placeholder="Select Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="caseDescription">Description</Label>
            <Textarea id="caseDescription" value={newCase.description} onChange={(e) => setNewCase({ ...newCase, description: e.target.value })} placeholder="Detailed description of the incident" rows={3} />
          </div>
          <div>
            <Label htmlFor="assignedTo">Assigned To</Label>
            <Input id="assignedTo" value={newCase.assigned_to} onChange={(e) => setNewCase({ ...newCase, assigned_to: e.target.value })} placeholder="e.g., John Doe" />
          </div>
        </div>
        <Button onClick={handleCreateCase} disabled={isLoading || !newCase.title} className="mt-4">
          Create Case
        </Button>
      </div>

      <div className="flex-1 min-h-0 mt-4">
        <h3 className="text-lg font-semibold mb-2">All Cases</h3>
        <div className="bg-card rounded-lg shadow-sm h-full overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cases.map((caseItem) => (
                <TableRow key={caseItem.id}>
                  <TableCell>{caseItem.id}</TableCell>
                  <TableCell>{caseItem.title}</TableCell>
                  <TableCell>{caseItem.status}</TableCell>
                  <TableCell>{caseItem.severity}</TableCell>
                  <TableCell>{caseItem.assigned_to || 'Unassigned'}</TableCell>
                  <TableCell>{new Date(caseItem.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" onClick={() => setSelectedCase(caseItem)}>View / Edit</Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[800px]">
                        <DialogHeader>
                          <DialogTitle>Case Details: {selectedCase?.title}</DialogTitle>
                        </DialogHeader>
                        {selectedCase && (
                          <div className="grid gap-4 py-4">
                            <p><strong>Description:</strong> {selectedCase.description}</p>
                            <p><strong>Status:</strong> {selectedCase.status}</p>
                            <p><strong>Severity:</strong> {selectedCase.severity}</p>
                            <p><strong>Assigned To:</strong> {selectedCase.assigned_to || 'Unassigned'}</p>
                            <p><strong>Created At:</strong> {new Date(selectedCase.created_at).toLocaleString()}</p>
                            <p><strong>Updated At:</strong> {new Date(selectedCase.updated_at).toLocaleString()}</p>
                            
                            <h4 className="font-semibold mt-2">Update Case</h4>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label htmlFor="updateStatus">Status</Label>
                                <Select value={updateStatus || selectedCase.status} onValueChange={setUpdateStatus}>
                                  <SelectTrigger id="updateStatus">
                                    <SelectValue placeholder="Update Status" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="new">New</SelectItem>
                                    <SelectItem value="in_progress">In Progress</SelectItem>
                                    <SelectItem value="resolved">Resolved</SelectItem>
                                    <SelectItem value="closed">Closed</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label htmlFor="updateAssignee">Assignee</Label>
                                <Input id="updateAssignee" value={updateAssignee || selectedCase.assigned_to || ''} onChange={(e) => setUpdateAssignee(e.target.value)} />
                              </div>
                            </div>
                            <Button onClick={() => handleUpdateCase(selectedCase.id, { status: updateStatus || selectedCase.status, assigned_to: updateAssignee || selectedCase.assigned_to })}>
                              <Edit className="mr-2 h-4 w-4" /> Update
                            </Button>

                            <h4 className="font-semibold mt-4">Notes</h4>
                            <div className="space-y-2 max-h-40 overflow-y-auto border p-2 rounded">
                                {selectedCase.notes.map((note, idx) => (
                                    <div key={idx} className="text-sm bg-gray-50 p-2 rounded">
                                        <p className="font-medium">{new Date(note.timestamp).toLocaleString()}</p>
                                        <p>{note.note}</p>
                                    </div>
                                ))}
                            </div>
                            <Textarea value={noteContent} onChange={(e) => setNoteContent(e.target.value)} placeholder="Add a new note..." />
                            <Button onClick={() => handleAddNote(selectedCase.id)} disabled={!noteContent}>Add Note</Button>

                            <h4 className="font-semibold mt-4">Timeline</h4>
                            <div className="space-y-2 max-h-40 overflow-y-auto border p-2 rounded">
                                {selectedCase.timeline.length > 0 ? (
                                    selectedCase.timeline.map((item, idx) => (
                                        <div key={idx} className="text-sm bg-gray-50 p-2 rounded">
                                            <p className="font-medium">{new Date(item.timestamp).toLocaleString()}</p>
                                            <p>{item.event}</p>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-muted-foreground">No timeline events.</p>
                                )}
                            </div>

                            <h4 className="font-semibold mt-4">Playbook Status</h4>
                            <div className="space-y-2 max-h-40 overflow-y-auto border p-2 rounded">
                                {Object.keys(selectedCase.playbook_status).length > 0 ? (
                                    Object.entries(selectedCase.playbook_status).map(([playbookName, status], idx) => (
                                        <div key={idx} className="text-sm bg-gray-50 p-2 rounded">
                                            <p className="font-medium"><strong>{playbookName}:</strong> {status.status} at {new Date(status.timestamp).toLocaleString()}</p>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-muted-foreground">No playbooks executed.</p>
                                )}
                            </div>
                            <Button onClick={() => handleExecutePlaybook(selectedCase.id)}>
                                <Play className="mr-2 h-4 w-4" /> Execute Default Playbook
                            </Button>

                          </div>
                        )}
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setSelectedCase(null)}>Close</Button>
                        </DialogFooter>
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

export default CaseManagementPage;
