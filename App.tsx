
import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Search, 
  Settings, 
  Radar
} from 'lucide-react';
import { 
  HashRouter as Router, 
  Routes, 
  Route, 
  useLocation, 
  useNavigate
} from 'react-router-dom';
import { TabType, Device } from './types';
import { INITIAL_DEVICES, NAV_ITEMS } from './constants';
import DeviceItem from './components/DeviceItem';
import TerminalComponent from './components/TerminalComponent';
import SecurityDashboard from './components/SecurityDashboard';
import NetworkStats from './components/NetworkStats';
import DeviceDetail from './components/DeviceDetail';

const AppContent: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isScanning, setIsScanning] = useState(false);
  const [devices, setDevices] = useState<Device[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchDevices = async () => {
    try {
      const response = await fetch('http://127.0.0.1:49152/api/devices');
      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (error) {
      console.error('Failed to fetch devices', error);
      // Fallback to initial if needed, or keep empty
    }
  };

  useEffect(() => {
    fetchDevices();
    // Auto-trigger a real scan on start to populate list immediately if empty
    fetch('http://127.0.0.1:49152/api/scan', { method: 'POST' }).catch(() => {});
    
    const interval = setInterval(fetchDevices, 1500); // Poll faster
    return () => clearInterval(interval);
  }, []);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      await fetch('http://127.0.0.1:49152/api/scan', { method: 'POST' });
      // Scanning happens in background, polling updates UI
    } catch (e) {
      console.error("Scan trigger failed", e);
    }
    
    // Auto turn off spinner after a while or handle status checks
    setTimeout(() => {
      setIsScanning(false);
    }, 5000);
  };

  const filteredDevices = devices.filter(d => 
    d.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    d.ip.includes(searchQuery) ||
    d.vendor.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/' || path.startsWith('/device')) return 'devices';
    if (path.startsWith('/network')) return 'network';
    if (path.startsWith('/security')) return 'security';
    if (path.startsWith('/terminal')) return 'terminal';
    return 'devices';
  };

  const activeTab = getActiveTab();
  const isDetailView = location.pathname.startsWith('/device/');

  return (
    <div className="flex flex-col h-screen max-w-md mx-auto bg-white shadow-2xl overflow-hidden relative border-x border-gray-100">
      {/* Header - Hidden on detail views to maximize space */}
      {!isDetailView && (
        <header className="bg-white px-4 pt-4 pb-3 sticky top-0 z-20">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <div className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-100">
                <Radar className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-black tracking-tighter text-gray-900 leading-none">NetGuardian</h1>
                <div className="flex items-center space-x-1 mt-1">
                  <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">v4.2.0-PRO</span>
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleScan}
                className={`p-2.5 rounded-full transition-all ${isScanning ? 'bg-blue-50' : 'bg-gray-50 hover:bg-gray-100 active:scale-90'}`}
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${isScanning ? 'animate-spin text-blue-600' : ''}`} />
              </button>
              <button className="p-2.5 bg-gray-50 rounded-full hover:bg-gray-100 active:scale-90">
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          {activeTab === 'devices' && (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center justify-between">
                <h2 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  {isScanning ? 'Synchronizing Nodes...' : `${devices.length} Devices Online`}
                </h2>
                {isScanning && (
                  <div className="text-blue-600 text-[10px] font-black animate-pulse flex items-center uppercase italic">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    Scanning...
                  </div>
                )}
              </div>
              
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Filter by IP, MAC or Vendor..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-gray-50 border-none rounded-2xl py-3 pl-11 pr-4 text-sm font-medium placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner"
                />
              </div>
            </div>
          )}
        </header>
      )}

      {/* Routed Content */}
      <main className="flex-1 overflow-hidden relative">
        <Routes>
          <Route path="/" element={
            <div className="h-full overflow-y-auto pb-24 scroll-smooth">
              {isScanning && (
                <div className="h-1 w-full bg-gray-50 overflow-hidden sticky top-0 z-10">
                  <div className="h-full bg-blue-500 animate-[loading_1.5s_infinite] w-1/3"></div>
                </div>
              )}
              <div className="divide-y divide-gray-50">
                {filteredDevices.map(device => (
                  <DeviceItem key={device.id} device={device} />
                ))}
              </div>
              {filteredDevices.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24 text-gray-300">
                  <Radar className="w-16 h-16 mb-4 opacity-10 animate-pulse" />
                  <p className="text-sm font-bold uppercase tracking-widest">Target not found</p>
                </div>
              )}
            </div>
          } />
          <Route path="/device/:id" element={<DeviceDetail />} />
          <Route path="/network" element={<NetworkStats />} />
          <Route path="/security" element={<SecurityDashboard />} />
          <Route path="/terminal" element={
            <TerminalComponent initialLines={[
              { text: 'NetGuardian Kernel v4.2.0-LTS [64-bit]', type: 'info' },
              { text: 'Optimized Environment: Python 3.11 / React 19', type: 'info' },
              { text: 'Type "help" for a list of security tools.', type: 'info' },
              { text: '--- Terminal Session Initiated ---', type: 'output' }
            ]} />
          } />
        </Routes>
      </main>

      {/* Bottom Navigation */}
      <nav className="bg-white/80 backdrop-blur-lg border-t border-gray-100 py-3 px-6 sticky bottom-0 z-30 flex justify-between items-center shadow-[0_-8px_30px_rgb(0,0,0,0.04)]">
        {NAV_ITEMS.map(item => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={`flex flex-col items-center justify-center transition-all flex-1 ${
                isActive ? 'text-blue-600 scale-105' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              <div className={`p-1.5 rounded-xl transition-colors ${isActive ? 'bg-blue-50' : 'bg-transparent'}`}>
                {item.icon}
              </div>
              <span className={`text-[9px] mt-1 font-black uppercase tracking-widest ${isActive ? 'opacity-100' : 'opacity-60'}`}>
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      <style>{`
        @keyframes loading {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;
