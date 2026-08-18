import api from './api';

const attackPathApi = import.meta.env.VITE_ATTACK_GRAPH_API_URL || '/api/governed-attack-paths';

const request = (config) => api({ ...config, url: `${attackPathApi}${config.url}` });

export const refreshAttackGraph = (limit = 200) => request({ method: 'post', url: `/refresh?limit=${limit}` });
export const analyzeAttackPath = (payload) => request({ method: 'post', url: '/analyze', data: payload });
