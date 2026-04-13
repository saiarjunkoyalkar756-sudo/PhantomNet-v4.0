import React, { useState } from 'react';
import siemService from '../services/siem.service';

const LogSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await siemService.searchLogs(query);
      setResults(response.data.results);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-4 mt-4">
      <h2 className="text-xl font-bold mb-4">Log Search</h2>
      <div className="flex">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-grow p-2 border border-gray-300 rounded-l-md"
          placeholder="Enter your PhantomQL query..."
        />
        <button
          onClick={handleSearch}
          className="bg-indigo-600 text-white px-4 py-2 rounded-r-md hover:bg-indigo-700"
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="mt-4 text-red-500">Error: {error}</div>}

      <div className="mt-4">
        {results.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source Host</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{log.message}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{log.source_host}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          !loading && <div className="mt-4 text-gray-500">No results to display.</div>
        )}
      </div>
    </div>
  );
};

export default LogSearch;
