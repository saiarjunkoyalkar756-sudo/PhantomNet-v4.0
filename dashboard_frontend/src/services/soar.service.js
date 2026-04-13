import axios from 'axios';

const API_URL = 'http://localhost:8001/soar-playbooks'; // Assuming gateway service is running on 8001

const getPlaybooks = () => {
  return axios.get(`${API_URL}/playbooks/`);
};

const getPlaybook = (id) => {
  return axios.get(`${API_URL}/playbooks/${id}`);
};

const createPlaybook = (playbook) => {
  return axios.post(`${API_URL}/playbooks/`, playbook);
};

const updatePlaybook = (id, playbook) => {
  return axios.put(`${API_URL}/playbooks/${id}`, playbook);
};

const deletePlaybook = (id) => {
  return axios.delete(`${API_URL}/playbooks/${id}`);
};

const runPlaybook = (id) => {
  return axios.post(`${API_URL}/playbooks/${id}/run`);
};

const getPlaybookRuns = (playbookId) => {
  return axios.get(`${API_URL}/playbook_runs/?playbook_id=${playbookId}`);
};


export default {
  getPlaybooks,
  getPlaybook,
  createPlaybook,
  updatePlaybook,
  deletePlaybook,
  runPlaybook,
  getPlaybookRuns,
};
