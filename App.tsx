
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

// Context for API URL
const ApiContext = React.createContext<{
  apiUrl: string;
  setApiUrl: (url: string) => void;
}>({ apiUrl: 'http://192.168.1.75:49152', setApiUrl: () => {} });

const ServerConfigScreen: React.FC<{ onConnect: () => void }> = ({ onConnect }) => {
  const { setApiUrl } = React.useContext(ApiContext);
  const [status, setStatus] = useState('Initializing Secure Node Discovery...');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const scanSubnet = async (prefix: string) => {
    // Port 49152 is our standard backend port
    const range = Array.from({ length: 254 }, (_, i) => i + 1);
    
    // Scan in concurrent batches for speed
    const batchSize = 30;
    for (let i = 0; i < range.length; i += batchSize) {
      const batch = range.slice(i, i + batchSize);
      const promises = batch.map(async (lastOctet) => {
        const ip = `${prefix}.${lastOctet}`;
        const url = `http://${ip}:49152`;
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 1200); // 1.2s per IP
          
          const res = await fetch(`${url}/api/network`, { signal: controller.signal });
          if (res.ok) {
            clearTimeout(timeoutId);
            return url;
          }
        } catch (e) {}
        return null;
      });

      const results = await Promise.all(promises);
      const found = results.find(r => r !== null);
      if (found) return found;
      
      setProgress(Math.round(((i + batchSize) / 254) * 100));
    }
    return null;
  };

  const startDiscovery = async () => {
    setError(null);
    setProgress(0);
    
    // Check common routers and local subnets
    const subnets = ['192.168.1', '192.168.0', '192.168.100', '10.0.0'];
    
    // Check cache first
    const saved = localStorage.getItem('netguardian_api_url') || 'http://192.168.1.75:49152';
    setStatus(`Attempting reconnection to ${saved.replace('http://', '').replace(':49152', '')}...`);
    try {
      const res = await fetch(`${saved}/api/network`, { mode: 'cors' } as any);
      if (res.ok) {
        setApiUrl(saved);
        onConnect();
        return;
      }
    } catch (e) {}

    // Not in cache? Scan deeply
    setStatus('No active uplink found. Starting Deep Network Pulse Scan...');
    for (const subnet of subnets) {
      setStatus(`Scanning Node Mesh: ${subnet}.x...`);
      const url = await scanSubnet(subnet);
      if (url) {
        setApiUrl(url);
        localStorage.setItem('netguardian_api_url', url);
        onConnect();
        return;
      }
    }
    
    setError('HQ NOT FOUND. Is the PC app (run_app.py) active on this Wi-Fi?');
    setStatus('Discovery Failed');
  };

  useEffect(() => {
    startDiscovery();
  }, []);

  return (
    <div className="min-h-screen bg-[#050b18] flex flex-col items-center justify-center p-6 text-white overflow-hidden relative">
      {/* Visual background glow */}
      <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-600/10 via-transparent to-transparent"></div>
      
      <div className="z-10 flex flex-col items-center space-y-12 w-full max-w-sm">
        <div className="relative group">
          <div className="w-24 h-24 bg-blue-600/20 rounded-3xl flex items-center justify-center border border-blue-500/30 animate-pulse transition-all group-hover:scale-110">
            <Settings className="w-12 h-12 text-blue-500" />
          </div>
          <div className="absolute inset-0 bg-blue-500/10 blur-2xl -z-10"></div>
        </div>

        <div className="text-center space-y-3">
          <h1 className="text-3xl font-black tracking-tighter text-white italic uppercase">NetGuardian <span className="text-blue-500">PRO</span></h1>
          <p className="text-gray-400 text-[10px] font-black uppercase tracking-[0.3em] h-4">
            {status}
          </p>
        </div>

        <div className="w-full space-y-6">
          <div className="h-1 w-full bg-blue-900/30 rounded-full overflow-hidden border border-white/5">
            <div 
              className="h-full bg-gradient-to-r from-blue-600 to-indigo-400 transition-all duration-300 ease-out shadow-[0_0_15px_rgba(59,130,246,0.6)]"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          
          <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-widest text-blue-500/50 px-1">
             <span className="animate-pulse">Mapping Local Mesh...</span>
             <span>{progress}%</span>
          </div>
        </div>

        {error && (
          <div className="p-5 bg-red-950/20 border border-red-500/20 rounded-3xl w-full text-center space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <p className="text-red-400 text-xs font-bold leading-relaxed px-4">{error}</p>
            <button 
              onClick={startDiscovery}
              className="w-full py-4 bg-red-600/80 hover:bg-red-500 text-white text-[10px] font-black rounded-2xl uppercase tracking-[0.2em] shadow-lg shadow-red-900/20 transition-all active:scale-95"
            >
              Restart Discovery Pulse
            </button>
          </div>
        )}

        <div className="absolute bottom-10 flex flex-col items-center space-y-2">
            <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-ping"></span>
                <span className="text-[9px] text-gray-400 font-bold uppercase tracking-[0.2em]">Auto-Discovery Active</span>
            </div>
        </div>
      </div>
    </div>
  );
};

const AppContent: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { apiUrl } = React.useContext(ApiContext);
  
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [devices, setDevices] = useState<Device[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Check connection on mount
  useEffect(() => {
    const saved = localStorage.getItem('netguardian_api_url') || apiUrl;
    // Simple check
    fetch(`${saved}/api/network`).then(res => {
      if(res.ok) setIsConnected(true);
    }).catch(() => {});
  }, []);

  const fetchDevices = async () => {
    if (!isConnected) return;
    try {
      const response = await fetch(`${apiUrl}/api/devices`);
      if (response.ok) {
        setDevices(await response.json());
      }
    } catch (error) { console.error(error); }
  };

  useEffect(() => {
    if (isConnected) {
      fetchDevices();
      const interval = setInterval(fetchDevices, 2000);
      return () => clearInterval(interval);
    }
  }, [isConnected, apiUrl]);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      await fetch(`${apiUrl}/api/scan`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
    setTimeout(() => setIsScanning(false), 5000);
  };

  if (!isConnected) {
    return <ServerConfigScreen onConnect={() => setIsConnected(true)} />;
  }

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
      {/* Header */}
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
                  <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">v4.3 Connected</span>
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button onClick={handleScan} className={`p-2.5 rounded-full transition-all ${isScanning ? 'bg-blue-50' : 'bg-gray-50 hover:bg-gray-100'}`}>
                <RefreshCw className={`w-5 h-5 text-gray-600 ${isScanning ? 'animate-spin text-blue-600' : ''}`} />
              </button>
              <button onClick={() => setIsConnected(false)} className="p-2.5 bg-gray-50 rounded-full hover:bg-gray-100">
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
              </div>
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Filter by IP..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-gray-50 border-none rounded-2xl py-3 pl-11 pr-4 text-sm font-medium outline-none"
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
              {isScanning && <div className="h-1 w-full bg-blue-500 animate-[loading_1.5s_infinite]"></div>}
              <div className="divide-y divide-gray-50">
                {filteredDevices.map(device => <DeviceItem key={device.id} device={device} />)}
              </div>
            </div>
          } />
          <Route path="/device/:id" element={<DeviceDetail apiUrl={apiUrl} />} />
          <Route path="/network" element={<NetworkStats apiUrl={apiUrl} />} />
          <Route path="/security" element={<SecurityDashboard apiUrl={apiUrl} />} />
          <Route path="/terminal" element={
            <TerminalComponent apiUrl={apiUrl} initialLines={[{ text: 'Remote Shell Active', type: 'success' }]} />
          } />
        </Routes>
      </main>

      {/* Nav */}
      <nav className="bg-white/80 backdrop-blur-lg border-t border-gray-100 py-3 px-6 sticky bottom-0 z-30 flex justify-between items-center shadow-[0_-8px_30px_rgb(0,0,0,0.04)]">
        {NAV_ITEMS.map(item => {
          const isActive = activeTab === item.id;
          return (
            <button key={item.id} onClick={() => navigate(item.path)} className={`flex flex-col items-center justify-center transition-all flex-1 ${isActive ? 'text-blue-600 scale-105' : 'text-gray-400'}`}>
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
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('netguardian_api_url') || 'http://192.168.1.75:49152');
  return (
    <Router>
      <ApiContext.Provider value={{ apiUrl, setApiUrl }}>
        <AppContent />
      </ApiContext.Provider>
    </Router>
  );
};

export default App;
