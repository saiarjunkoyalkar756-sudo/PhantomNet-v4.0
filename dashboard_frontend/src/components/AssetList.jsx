import React, { useState, useEffect } from 'react';
import vulnerabilityService from '../services/vulnerability.service';

const AssetList = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await vulnerabilityService.getAssets();
        setAssets(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchAssets();
  }, []);

  if (loading) {
    return <div>Loading assets...</div>;
  }

  if (error) {
    return <div>Error fetching assets: {error}</div>;
  }

  return (
    <div className="bg-white shadow rounded-lg p-4 mt-4">
      <h2 className="text-xl font-bold mb-4">Scanned Assets</h2>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset ID</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset Type</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Scanned</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {assets.map((asset) => (
            <tr key={asset.id}>
              <td className="px-6 py-4 whitespace-nowrap">{asset.asset_id}</td>
              <td className="px-6 py-4 whitespace-nowrap">{asset.asset_name}</td>
              <td className="px-6 py-4 whitespace-nowrap">{asset.asset_type}</td>
              <td className="px-6 py-4 whitespace-nowrap">{new Date(asset.last_scanned_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AssetList;
