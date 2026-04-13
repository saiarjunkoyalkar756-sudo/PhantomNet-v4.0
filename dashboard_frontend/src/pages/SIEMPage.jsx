import React from 'react';
import LogSearch from '../components/LogSearch';

const SIEMPage = () => {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">SIEM</h1>
      <p>This is the page for Security Information and Event Management.</p>
      <LogSearch />
    </div>
  );
};

export default SIEMPage;
