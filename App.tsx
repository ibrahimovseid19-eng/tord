
import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Search, 
  Radar
} from 'lucide-react';
import { 
  HashRouter as Router, 
  Routes, 
  Route, 
  useLocation, 
  useNavigate
} from 'react-router-dom';
import { Device } from './types';
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
  const [devices, setDevices] = useState<Device[]>(INITIAL_DEVICES);
  const [searchQuery, setSearchQuery] = useState('');
  const [networkInfo, setNetworkInfo] = useState({
    ssid: 'Analyzing Local Wi-Fi...',
    ip: '...',
    gateway: '...',
    status: 'Initializing'
  });

  // STANDALONE MODE: Local Mobile Discovery Logic
  useEffect(() => {
    // Simulate direct mobile hardware access
    const timer = setTimeout(() => {
      setNetworkInfo({
        ssid: 'External Android Node',
        ip: '192.168.1.42', 
        gateway: '192.168.1.1',
        status: 'Operational'
      });
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleScan = () => {
    setIsScanning(true);
    // Simulate high-speed mobile local ARP/Ping scan
    setTimeout(() => {
      setIsScanning(false);
    }, 4000);
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
    <div className="flex flex-col h-screen w-full md:max-w-md mx-auto bg-white shadow-2xl overflow-hidden relative md:border-x border-gray-100">
      {/* Standalone Header */}
      {!isDetailView && (
        <header className="bg-white px-4 pt-4 pb-3 sticky top-0 z-20">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <div className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-100">
                <Radar className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-black tracking-tighter text-gray-900 leading-none">NetGuardian <span className="text-blue-600">PRO</span></h1>
                <div className="flex items-center space-x-1 mt-1">
                  <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">{networkInfo.ssid}</span>
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleScan} 
                className={`p-2.5 rounded-full transition-all active:scale-90 ${isScanning ? 'bg-blue-50 text-blue-600 shadow-inner' : 'bg-gray-50 text-gray-400'}`}
              >
                <RefreshCw className={`w-5 h-5 ${isScanning ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {activeTab === 'devices' && (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center justify-between">
                <h2 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                  {isScanning ? 'Scanning Subnet...' : `${devices.length} Nodes Identified`}
                </h2>
                <span className="text-[9px] font-black text-blue-600 bg-blue-100/50 px-2 py-0.5 rounded-md">MOBILE KERNEL</span>
              </div>
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Filter network nodes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-gray-50 border-none rounded-2xl py-3 pl-11 pr-4 text-sm font-medium outline-none placeholder-gray-300"
                />
              </div>
            </div>
          )}
        </header>
      )}

      {/* Standalone Content */}
      <main className="flex-1 overflow-hidden relative">
        <Routes>
          <Route path="/" element={
            <div className="h-full overflow-y-auto pb-24 scroll-smooth">
              {isScanning && <div className="h-1 w-full bg-blue-500 animate-[loading_2s_infinite]"></div>}
              <div className="divide-y divide-gray-50">
                {filteredDevices.map(device => <DeviceItem key={device.id} device={device} />)}
              </div>
            </div>
          } />
          <Route path="/device/:id" element={<DeviceDetail apiUrl="" />} />
          <Route path="/network" element={<NetworkStats apiUrl="" />} />
          <Route path="/security" element={<SecurityDashboard apiUrl="" />} />
          <Route path="/terminal" element={
            <TerminalComponent apiUrl="" initialLines={[
              { text: 'NetGuardian Standalone Kernel v5.0.2', type: 'success' },
              { text: 'Operating Mode: Independent Mobile Node', type: 'info' },
              { text: 'Local Security Matrix: Stable', type: 'info' }
            ]} />
          } />
        </Routes>
      </main>

      {/* Nav */}
      <nav className="bg-white/90 backdrop-blur-md border-t border-gray-100 py-3 px-6 sticky bottom-0 z-30 flex justify-between items-center shadow-[0_-10px_40px_rgba(0,0,0,0.03)]">
        {NAV_ITEMS.map(item => {
          const isActive = activeTab === item.id;
          return (
            <button key={item.id} onClick={() => navigate(item.path)} className={`flex flex-col items-center justify-center transition-all flex-1 active:scale-95 ${isActive ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`p-1.5 rounded-xl transition-colors ${isActive ? 'bg-blue-50' : 'bg-transparent'}`}>{item.icon}</div>
              <span className={`text-[9px] mt-1 font-black uppercase tracking-widest ${isActive ? 'opacity-100' : 'opacity-60'}`}>{item.label}</span>
            </button>
          );
        })}
      </nav>
      <style>{`@keyframes loading { 0% { transform: translateX(-100%); } 100% { transform: translateX(300%); } }`}</style>
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
