import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { logoutUser } from '../features/auth/authSlice';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Layout = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated } = useSelector((state) => state.auth);

  const handleLogout = () => {
    dispatch(logoutUser());
  };

  if (!isAuthenticated) {
    return <Outlet />; // Render login/public routes without sidebar
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 text-white flex flex-col">
        <div className="p-4 text-2xl font-bold border-b border-gray-700">
          PhantomNet
        </div>
        <nav className="flex-1 px-2 py-4 space-y-2">
          <Link
            to="/dashboard"
            className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
          >
            Dashboard
          </Link>
          {user?.role === 'admin' && (
            <>
              <Link
                to="/admin"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Admin Panel
              </Link>
              <Link
                to="/admin/audit"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Audit Log
              </Link>
              <Link
                to="/ai-threat-brain"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                AI Threat Brain
              </Link>
              <Link
                to="/network-map"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Network Map
              </Link>
              <Link
                to="/attack-map"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Attack Map
              </Link>
              <Link
                to="/federation-settings"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Federation Settings
              </Link>
              <Link
                to="/blockchain"
                className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                Blockchain Viewer
              </Link>
            </>
          )}
          <Link
            to="/2fa-setup"
            className="block px-4 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white"
          >
            Manage 2FA
          </Link>
        </nav>
        <div className="p-4 border-t border-gray-700">
          <p className="text-sm text-gray-400">Logged in as:</p>
          <p className="font-medium">{user?.username}</p>
          <button
            onClick={handleLogout}
            className="mt-2 w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex justify-between items-center p-4 bg-white border-b shadow-sm">
          <h1 className="text-xl font-semibold">Dashboard Overview</h1>
          {/* Potentially add user profile/settings here */}
        </header>
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200 p-4">
          <Outlet /> {/* This is where the routed components will be rendered */}
        </main>
      </div>
    </div>
  );
};

export default Layout;
