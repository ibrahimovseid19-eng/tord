
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
  const { apiUrl, setApiUrl } = React.useContext(ApiContext);
  const [ip, setIp] = useState(apiUrl.replace('http://', '').replace(':49152', ''));
  const [status, setStatus] = useState<'idle' | 'checking' | 'error'>('idle');

  const checkConnection = async () => {
    setStatus('checking');
    const url = `http://${ip}:49152`;
    try {
      // Short timeout
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 2000);
      
      const res = await fetch(`${url}/api/network`, { signal: controller.signal });
      clearTimeout(id);
      
      if (res.ok) {
        setApiUrl(url);
        localStorage.setItem('netguardian_api_url', url);
        onConnect();
      } else {
        setStatus('error');
      }
    } catch (e) {
      setStatus('error');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-slate-900 text-white p-6">
      <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-500/20">
        <Settings className="w-8 h-8 text-white" />
      </div>
      <h1 className="text-2xl font-black tracking-tight mb-2">Connect to Desktop</h1>
      <p className="text-slate-400 text-center text-sm mb-8">
        Enter the IP address shown on your PC's NetGuardian window (run_app.py).
      </p>
      
      <div className="w-full max-w-xs space-y-4">
        <div>
          <label className="text-xs font-bold uppercase text-slate-500 mb-1 block">Desktop IP Address</label>
          <input 
            type="text" 
            value={ip}
            onChange={e => setIp(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl p-4 text-center font-mono text-lg font-bold tracking-wider focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="192.168.1.xxx"
          />
        </div>
        
        <button 
          onClick={checkConnection}
          disabled={status === 'checking'}
          className="w-full bg-blue-600 hover:bg-blue-500 active:scale-95 transition-all p-4 rounded-xl font-bold uppercase tracking-widest flex items-center justify-center"
        >
          {status === 'checking' ? <RefreshCw className="animate-spin w-5 h-5" /> : 'Connect'}
        </button>
        
        {status === 'error' && (
          <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg text-red-400 text-xs text-center font-bold">
            Connection Failed. Check IP & Firewall.
          </div>
        )}
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
    <div className="flex flex-col h-screen max-w-md mx-auto bg-white shadow-2xl overflow-hidden relative border-x border-gray-100">
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
