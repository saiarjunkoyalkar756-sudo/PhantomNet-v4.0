import { io } from 'socket.io-client';
import { useStore } from '@/store/useStore';

// In a real application, replace this with your actual WebSocket server URL
const SOCKET_SERVER_URL = 'http://localhost:3001'; // Example for a separate WS server

const eventTypes = [
    "Threat Detected", "Anomaly Alert", "Agent Offline", "Policy Violation",
    "Login Failure", "Data Exfiltration Attempt", "C2 Communication", "Malware Found"
];
const severities = ["High", "Medium", "Low", "Informational"];
const agents = ["agent-alpha-1", "agent-beta-2", "agent-gamma-3", "agent-delta-4"];
const ips = ["192.168.1.10", "10.0.0.5", "172.16.3.20", "203.0.113.45"];

const generateSyntheticEvent = () => {
    const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    const severity = severities[Math.floor(Math.random() * severities.length)];
    const agent = agents[Math.floor(Math.random() * agents.length)];
    const ip = ips[Math.floor(Math.random() * ips.length)];

    return {
        id: Date.now() + Math.random(),
        timestamp: new Date().toISOString(),
        type,
        severity,
        agent,
        sourceIp: ip,
        message: `${type} from ${agent} at ${ip}. Severity: ${severity}.`,
        aiInsight: Math.random() > 0.5 ? "Suspicious activity pattern identified." : null,
    };
};

export const initWebSocketSimulator = () => {
    // In a real setup, you would connect to a real WebSocket server
    // const socket = io(SOCKET_SERVER_URL);
    // socket.on('connect', () => console.log('Connected to WebSocket server'));
    // socket.on('event', (event) => useStore.getState().addEvent(event));

    console.log("WebSocket Simulator Initialized: Generating synthetic events.");

    // Simulate real-time events by pushing synthetic data every few seconds
    const intervalId = setInterval(() => {
        const event = generateSyntheticEvent();
        useStore.getState().addEvent(event);
    }, 1500); // Generate a new event every 1.5 seconds

    return () => clearInterval(intervalId); // Cleanup function
};
