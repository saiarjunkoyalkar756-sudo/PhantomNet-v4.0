import React, { useState, useEffect, useRef } from 'react';
import PageHeader from '@/components/shared/PageHeader';
import { motion } from 'framer-motion';
import { Terminal } from 'lucide-react';
import LiveFeedList from '@/features/events/components/LiveFeedList';
import EventDetailDrawer from '@/features/events/components/EventDetailDrawer';
import FilterToolbar from '@/features/events/components/FilterToolbar';
import { useStore } from '@/store/useStore'; // Import useStore
import io from 'socket.io-client'; // Import socket.io-client

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8001';

const EventStreamViewer = () => {
  const allEvents = useStore((state) => state.events); // Get all events from store
  const addEvent = useStore((state) => state.addEvent); // Get addEvent function
  const [isPaused, setIsPaused] = useState(false);
  const [filters, setFilters] = useState({ severity: '', type: '', agent: '' });
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [displayEvents, setDisplayEvents] = useState([]); // Events to display in the list

  // Ref for the WebSocket client to maintain its instance across renders
  const socketRef = useRef(null);

  useEffect(() => {
    // --- WebSocket Connection ---
    if (!socketRef.current) {
        socketRef.current = io(`${WS_BASE_URL}/ws/events`); // Connect to the WebSocket endpoint

        socketRef.current.on('connect', () => {
            console.log('Connected to WebSocket server');
        });

        socketRef.current.on('message', (message) => {
            try {
                const event = JSON.parse(message);
                addEvent(event); // Add event to Zustand store
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        });

        socketRef.current.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
        });

        socketRef.current.on('error', (err) => {
            console.error('WebSocket error:', err);
        });
    }

    // Cleanup function: disconnect from WebSocket when component unmounts
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [addEvent]); // Re-run effect if addEvent changes (should be stable)

  const togglePause = () => setIsPaused(!isPaused);

  useEffect(() => {
    // Filter events whenever allEvents or filters change
    let newDisplayEvents = allEvents.filter(event => {
      return (
        (filters.severity === '' || event.severity === filters.severity) &&
        // Note: event.event_type is used from backend, not 'type'
        (filters.type === '' || event.event_type === filters.type) && 
        (filters.agent === '' || event.agent_id === filters.agent) // Use agent_id from backend
      );
    });

    // If stream is paused, only update the displayed events when it's unpaused or filters change
    if (!isPaused) {
      setDisplayEvents(newDisplayEvents);
    }
  }, [allEvents, filters, isPaused]);


  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="font-sans h-full flex flex-col"
    >
      <PageHeader 
        title="EVENT STREAM CONSOLE"
        subtitle="Real-time security event feed from all integrated sources."
        actions={
            <div className="flex items-center space-x-2">
                <Terminal className="text-primary animate-pulse" size={20} />
                <span className="text-primary font-mono text-sm">LIVE</span>
            </div>
        }
      />

      <FilterToolbar
        isPaused={isPaused}
        togglePause={togglePause}
        filters={filters}
        setFilters={setFilters}
      />

      <div className="flex-1 min-h-0"> {/* min-h-0 to allow flex-1 to shrink */}
        <LiveFeedList events={displayEvents} onEventClick={setSelectedEvent} />
      </div>

      <EventDetailDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </motion.div>
  );
};

export default EventStreamViewer;
