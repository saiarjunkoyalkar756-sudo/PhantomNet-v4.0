import { create } from 'zustand';

export const useStore = create((set) => ({
  events: [],
  addEvent: (event) => set((state) => ({
    events: [event, ...state.events].slice(0, 100) // Keep last 100 events
  })),
}));
