import api from './api';

const governedResponseApi = import.meta.env.VITE_SOAR_API_URL || '/api/soar';

const request = (config) => api({ ...config, url: `${governedResponseApi}/governed-containment${config.url}` });

export const fetchContainmentRequests = () => request({ method: 'get', url: '/requests' });
export const createContainmentRequest = (payload) => request({ method: 'post', url: '/requests', data: payload });
export const fetchContainmentPreflight = (requestId) => request({ method: 'get', url: `/requests/${requestId}/preflight` });
export const decideContainmentRequest = (requestId, payload) => request({ method: 'post', url: `/requests/${requestId}/decision`, data: payload });
export const executeContainmentRequest = (requestId) => request({ method: 'post', url: `/requests/${requestId}/execute` });
export const rollbackContainmentRequest = (requestId) => request({ method: 'post', url: `/requests/${requestId}/rollback` });
export const verifyContainmentAudit = () => request({ method: 'get', url: '/audit/verify' });

export const fetchDefensePolicies = () => request({ method: 'get', url: '/autonomous-defense/policies' });
export const fetchDefenseDecisions = () => request({ method: 'get', url: '/autonomous-defense/decisions' });
export const evaluateDefenseDetection = (detectionId) => request({ method: 'post', url: `/autonomous-defense/detections/${detectionId}/evaluate` });
