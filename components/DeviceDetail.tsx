
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, Clock, HardDrive, Network, Tag, Info, Cpu, Smartphone, Monitor, Laptop, Printer, Router } from 'lucide-react';
import { INITIAL_DEVICES, DEVICE_ICONS } from '../constants';

const DeviceDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [device, setDevice] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [scanResult, setScanResult] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchDevice = async () => {
      try {
        const res = await fetch('http://127.0.0.1:49152/api/devices');
        if (res.ok) {
          const devices = await res.json();
          // Find device by mac (id)
          const found = devices.find((d: any) => d.id === id || d.mac === id);
          setDevice(found);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDevice();
  }, [id]);

  const handlePortScan = async () => {
    if (!device) return;
    setScanResult("Scanning...");
    try {
      const res = await fetch('http://127.0.0.1:49152/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'ports', args: [device.ip] })
      });
      const data = await res.json();
      setScanResult(data.output);
    } catch {
      setScanResult("Scan failed.");
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading profile...</div>;

  if (!device) {
    return (
      <div className="p-8 text-center h-full flex flex-col items-center justify-center">
        <p className="text-gray-500">Device not found in registry.</p>
        <button 
          onClick={() => navigate('/')}
          className="mt-4 text-blue-600 font-bold bg-blue-50 px-6 py-2 rounded-xl"
        >
          Go Back
        </button>
      </div>
    );
  }
  
  // Helper to get icon safely
  const getIcon = (type: string) => {
    // @ts-ignore
    return DEVICE_ICONS[type] || DEVICE_ICONS['iot'];
  };

  return (
    <div className="bg-gray-50 h-full overflow-y-auto pb-24">
      {/* Detail Header */}
      <div className="bg-white p-4 sticky top-0 z-10 border-b border-gray-100 flex items-center space-x-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors active:scale-90"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <h2 className="font-bold text-gray-900">Device Profile</h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Profile Card */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col items-center text-center">
          <div className={`p-6 rounded-3xl mb-4 ${device.status === 'online' ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
             {/* Dynamic Icon */}
             {React.cloneElement(getIcon(device.type) as React.ReactElement, { className: 'w-12 h-12' })}
          </div>
          <h1 className="text-xl font-black text-gray-900 tracking-tight">{device.name || 'Unknown Device'}</h1>
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">{device.vendor || 'Unknown Vendor'}</p>
          <div className="flex items-center mt-4 space-x-2">
            <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${
              device.status === 'online' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
            }`}>
              {device.status}
            </span>
            <span className="text-[10px] text-gray-300 font-bold">•</span>
            <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">{device.type}</span>
          </div>
        </div>

        {/* Technical Specification Grid */}
        <div className="grid grid-cols-1 gap-3">
          <InfoItem 
            icon={<Network className="w-4 h-4 text-blue-500" />} 
            label="IP Address" 
            value={device.ip} 
          />
          <InfoItem 
            icon={<Tag className="w-4 h-4 text-indigo-500" />} 
            label="MAC Address" 
            value={device.mac} 
          />
          <InfoItem 
            icon={<HardDrive className="w-4 h-4 text-purple-500" />} 
            label="Operating System" 
            value={device.os || 'Unknown'} 
          />
          <InfoItem 
            icon={<Clock className="w-4 h-4 text-orange-500" />} 
            label="Last Active" 
            value={device.lastSeen || 'Never'} 
          />
        </div>

        {/* Security Summary Section */}
        <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm">
           <div className="flex items-center justify-between mb-6">
             <div className="flex items-center space-x-2">
                <Shield className="w-5 h-5 text-emerald-500" />
                <h3 className="font-bold text-sm text-gray-900 uppercase tracking-tight">Security Audit</h3>
             </div>
             <button 
                onClick={handlePortScan}
                className="text-[10px] font-black text-white bg-emerald-500 hover:bg-emerald-600 px-3 py-1.5 rounded-lg transition-colors"
              >
                SCAN PORTS
              </button>
           </div>
           
           {scanResult ? (
             <div className="bg-gray-900 rounded-xl p-4 font-mono text-xs text-green-400 overflow-x-auto whitespace-pre">
               {scanResult}
             </div>
           ) : (
             <div className="space-y-4">
               <div className="flex items-center justify-between">
                 <span className="text-xs font-semibold text-gray-500">Port Scrutiny</span>
                 <span className="text-xs font-black text-gray-400">PENDING</span>
               </div>
               <div className="flex items-center justify-between">
                 <span className="text-xs font-semibold text-gray-500">Vulnerability Flags</span>
                 <span className="text-xs font-black text-gray-900 uppercase">None Detected</span>
               </div>
               <div className="w-full bg-gray-50 h-2 rounded-full overflow-hidden shadow-inner">
                 <div className="bg-gray-200 h-full w-full"></div>
               </div>
             </div>
           )}
           
           <p className="text-[9px] text-gray-400 mt-5 leading-relaxed font-medium">
             Active analysis required. Click Scan Ports to verify open services on this node.
           </p>
        </div>
      </div>
    </div>
  );
};

const InfoItem: React.FC<{ icon: React.ReactNode, label: string, value: string }> = ({ icon, label, value }) => (
  <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center space-x-4">
    <div className="bg-gray-50 p-3 rounded-xl">
      {icon}
    </div>
    <div className="flex-1">
      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{label}</p>
      <p className="text-sm font-bold text-gray-900 tabular-nums">{value}</p>
    </div>
  </div>
);

export default DeviceDetail;
