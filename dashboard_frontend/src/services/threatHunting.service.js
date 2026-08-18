import api from './api';

const huntApi = import.meta.env.VITE_THREAT_HUNT_API_URL || '/api/threat-hunting';

const request = (config) => api({ ...config, url: `${huntApi}${config.url}` });

export const executeHunt = (payload) => request({ method: 'post', url: '/hunts/execute', data: payload });
export const fetchSavedHunts = () => request({ method: 'get', url: '/hunts/saved' });
export const saveHunt = (payload) => request({ method: 'post', url: '/hunts/saved', data: payload });
export const executeSavedHunt = (huntId) => request({ method: 'post', url: `/hunts/saved/${huntId}/execute` });
export const fetchAutomatedHunts = () => request({ method: 'get', url: '/hunts/automated' });
export const fetchHuntDashboardSummary = () => request({ method: 'get', url: '/dashboard/summary' });
