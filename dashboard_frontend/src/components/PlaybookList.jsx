import React, { useState, useEffect } from 'react';
import soarService from '../services/soar.service';

const PlaybookList = () => {
  const [playbooks, setPlaybooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlaybooks = async () => {
      try {
        const response = await soarService.getPlaybooks();
        setPlaybooks(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchPlaybooks();
  }, []);

  if (loading) {
    return <div>Loading playbooks...</div>;
  }

  if (error) {
    return <div>Error fetching playbooks: {error}</div>;
  }

  return (
    <div className="bg-white shadow rounded-lg p-4 mt-4">
      <h2 className="text-xl font-bold mb-4">Available Playbooks</h2>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {playbooks.map((playbook) => (
            <tr key={playbook.id}>
              <td className="px-6 py-4 whitespace-nowrap">{playbook.name}</td>
              <td className="px-6 py-4 whitespace-nowrap">{playbook.description}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    playbook.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {playbook.status}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button
                  onClick={() => soarService.runPlaybook(playbook.id)}
                  className="text-indigo-600 hover:text-indigo-900"
                >
                  Run
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PlaybookList;
