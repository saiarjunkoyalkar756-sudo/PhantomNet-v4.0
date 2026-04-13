import axios from 'axios';

const API_URL = 'http://localhost:8001/phantomql-engine'; // Assuming gateway service is running on 8001

const searchLogs = (query) => {
  return axios.post(`${API_URL}/query/`, { query_string: query });
};

export default {
  searchLogs,
};
