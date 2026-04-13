import axios from 'axios';

const API_URL = 'http://localhost:8001/soc-copilot'; // Assuming gateway service is running on 8001

const getExplanation = (query) => {
  return axios.post(`${API_URL}/explain_alert/`, { query });
};

export default {
  getExplanation,
};
