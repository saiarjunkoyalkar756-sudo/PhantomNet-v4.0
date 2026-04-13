import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { fetchUsers, updateUserRole, disableUser, enableUser } from '../features/users/userSlice';
import SecurityInsights from './SecurityInsights';
import HealthStatus from './HealthStatus';
import AgentList from './AgentList';
import { toast } from 'react-toastify';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { users, loading, error } = useSelector((state) => state.users);

  useEffect(() => {
    if (user && user.role === 'admin') {
      dispatch(fetchUsers());
    } else {
      // Redirect or show error if not admin
      toast.error('Access Denied: You must be an administrator to view this page.');
      navigate('/dashboard'); // Redirect to dashboard if not admin
    }
  }, [user, dispatch, navigate]);

  const handleRoleChange = async (userId, newRole) => {
    const resultAction = await dispatch(updateUserRole({ userId, role: newRole }));
    if (updateUserRole.fulfilled.match(resultAction)) {
      toast.success('User role updated successfully!');
    } else {
      toast.error(`Failed to update user role: ${resultAction.payload}`);
    }
  };

  const handleDisableUser = async (userId) => {
    if (window.confirm('Are you sure you want to disable this user?')) {
      const resultAction = await dispatch(disableUser(userId));
      if (disableUser.fulfilled.match(resultAction)) {
        toast.success('User disabled successfully!');
      } else {
        toast.error(`Failed to disable user: ${resultAction.payload}`);
      }
    }
  };

  const handleEnableUser = async (userId) => {
    if (window.confirm('Are you sure you want to enable this user?')) {
      const resultAction = await dispatch(enableUser(userId));
      if (enableUser.fulfilled.match(resultAction)) {
        toast.success('User enabled successfully!');
      } else {
        toast.error(`Failed to enable user: ${resultAction.payload}`);
      }
    }
  };

  if (loading) {
    return <div className="p-4">Loading users...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="admin-dashboard-container p-4">
      <h2 className="text-2xl font-bold mb-4">Admin Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <SecurityInsights />
        <HealthStatus />
      </div>

      <div className="mt-6">
        <AgentList />
      </div>

      <h3 className="text-xl font-bold mt-6 mb-3">User Management</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white">
          <thead>
            <tr>
              <th className="py-2 px-4 border-b">ID</th>
              <th className="py-2 px-4 border-b">Username</th>
              <th className="py-2 px-4 border-b">Role</th>
              <th className="py-2 px-4 border-b">2FA Enforced</th>
              <th className="py-2 px-4 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="py-2 px-4 border-b">{u.id}</td>
                <td className="py-2 px-4 border-b">{u.username}</td>
                <td className="py-2 px-4 border-b">
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    className="border rounded p-1"
                  >
                    <option value="user">User</option>
                    <option value="analyst">Analyst</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td className="py-2 px-4 border-b">
                  {u.twofa_enforced ? 'Yes' : 'No'}
                </td>
                <td className="py-2 px-4 border-b">
                  <button
                    onClick={() => handleDisableUser(u.id)}
                    className="bg-red-500 text-white px-3 py-1 rounded mr-2"
                  >
                    Disable
                  </button>
                  <button
                    onClick={() => handleEnableUser(u.id)}
                    className="bg-green-500 text-white px-3 py-1 rounded"
                  >
                    Enable
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className="text-xl font-bold mt-6 mb-3">Audit Log</h3>
      <p>View recent system activities and administrative actions.</p>
      <button
        onClick={() => navigate('/admin/audit')}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        View Audit Log
      </button>

      <h3 className="text-xl font-bold mt-6 mb-3">AI Threat Brain</h3>
      <p>Simulate attacks and view AI-powered threat analysis.</p>
      <button
        onClick={() => navigate('/ai-threat-brain')}
        className="bg-purple-500 text-white px-4 py-2 rounded"
      >
        Go to AI Threat Brain
      </button>

      <h3 className="text-xl font-bold mt-6 mb-3">Network Map</h3>
      <p>Visualize the network of PhantomNet agents.</p>
      <button
        onClick={() => navigate('/network-map')}
        className="bg-teal-500 text-white px-4 py-2 rounded"
      >
        View Network Map
      </button>

      <h3 className="text-xl font-bold mt-6 mb-3">Real-Time Attack Map</h3>
      <p>Visualize incoming attacks in real-time on a world map.</p>
      <button
        onClick={() => navigate('/attack-map')}
        className="bg-red-700 text-white px-4 py-2 rounded"
      >
        View Attack Map
      </button>

      <h3 className="text-xl font-bold mt-6 mb-3">Federation Settings</h3>
      <p>Manage agent federation, CA, and bootstrap tokens.</p>
      <button
        onClick={() => navigate('/federation-settings')}
        className="bg-indigo-500 text-white px-4 py-2 rounded"
      >
        Manage Federation
      </button>
    </div>
  );
};

export default AdminDashboard;