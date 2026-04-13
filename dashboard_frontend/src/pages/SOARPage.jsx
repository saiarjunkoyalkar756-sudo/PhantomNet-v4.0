import React from 'react';
import PlaybookList from '../components/PlaybookList';

const SOARPage = () => {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">SOAR Playbooks</h1>
      <p>This is the page for Security Orchestration, Automation, and Response.</p>
      <PlaybookList />
    </div>
  );
};

export default SOARPage;
