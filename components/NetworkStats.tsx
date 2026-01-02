
import React, { useState, useEffect } from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { Wifi, Globe, Activity, ArrowUpRight, ArrowDownLeft, Zap } from 'lucide-react';

interface DataPoint {
  time: string;
  down: number;
  up: number;
}

interface NetworkInfo {
  ip: string;
  gateway: string;
  ssid: string;
}

const NetworkStats: React.FC = () => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [latestSpeeds, setLatestSpeeds] = useState({ down: 0, up: 0 });
  const [info, setInfo] = useState<NetworkInfo>({ ip: '...', gateway: '...', ssid: '...' });
  
  // Use refs to track values inside the interval closure without re-creating the interval
  const lastBytesRef = React.useRef({ sent: 0, recv: 0, time: Date.now() });

  useEffect(() => {
    // Initial data seed
    const initialData: DataPoint[] = Array.from({ length: 20 }, (_, i) => ({
      time: new Date(Date.now() - (20 - i) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      down: 0,
      up: 0,
    }));
    setData(initialData);

    const fetchData = async () => {
      try {
        const res = await fetch('http://127.0.0.1:49152/api/network');
        if (!res.ok) return;
        const json = await res.json();
        
        setInfo({ ip: json.ip, gateway: json.gateway, ssid: json.ssid });

        const now = Date.now();
        const prev = lastBytesRef.current;
        const timeDiff = (now - prev.time) / 1000; // seconds
        
        // Only calculate if we have a valid previous reading (not the very first 0)
        // and avoid division by zero
        let downSpeed = 0;
        let upSpeed = 0;

        if (prev.time > 0 && timeDiff > 0 && prev.sent > 0) {
          // Calculate Mbps
          downSpeed = ((json.bytes_recv - prev.recv) * 8) / (1000000 * timeDiff);
          upSpeed = ((json.bytes_sent - prev.sent) * 8) / (1000000 * timeDiff);
          
          // Clamp negative values (restarts etc)
          downSpeed = Math.max(0, downSpeed);
          upSpeed = Math.max(0, upSpeed);
        }
        
        setLatestSpeeds({ down: downSpeed, up: upSpeed });
        
        // Update Chart Data
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        setData(prevData => {
          const newData = [...prevData, { time: timeStr, down: downSpeed, up: upSpeed }];
          return newData.slice(-30); // Keep last 30 points for smoother history
        });
        
        // Update Ref for next tick
        lastBytesRef.current = { sent: json.bytes_sent, recv: json.bytes_recv, time: now };

      } catch (e) {
        console.error("Network stats error", e);
      }
    };

    // Run every 1 second for "Live" feel
    const interval = setInterval(fetchData, 1000);
    fetchData(); // Initial call
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-gray-50 h-full overflow-y-auto pb-24">
      {/* Real-time KPI Cards */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm transition-all">
          <div className="flex items-center space-x-2 text-blue-600 mb-2">
            <ArrowDownLeft className="w-4 h-4" />
            <span className="text-[10px] font-bold uppercase tracking-wider">Download</span>
          </div>
          <div className="flex items-baseline space-x-1">
            <p className="text-2xl font-black text-gray-900 tabular-nums">
              {latestSpeeds.down.toFixed(1)}
            </p>
            <span className="text-xs font-medium text-gray-500">Mbps</span>
          </div>
          <div className="mt-2 flex items-center text-[10px] text-green-600 font-bold">
            <Zap className="w-3 h-3 mr-1" />
            <span>STABLE CONNECTION</span>
          </div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm transition-all">
          <div className="flex items-center space-x-2 text-indigo-600 mb-2">
            <ArrowUpRight className="w-4 h-4" />
            <span className="text-[10px] font-bold uppercase tracking-wider">Upload</span>
          </div>
          <div className="flex items-baseline space-x-1">
            <p className="text-2xl font-black text-gray-900 tabular-nums">
              {latestSpeeds.up.toFixed(1)}
            </p>
            <span className="text-xs font-medium text-gray-500">Mbps</span>
          </div>
          <div className="mt-2 flex items-center text-[10px] text-indigo-400 font-bold">
            <Activity className="w-3 h-3 mr-1" />
            <span>8ms LATENCY</span>
          </div>
        </div>
      </div>

        {/* Live Chart Container */}
      <div className="bg-white p-5 rounded-3xl border border-gray-100 shadow-sm mb-6 relative overflow-hidden">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="font-bold text-gray-900">Traffic Analysis</h3>
            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-0.5">Live Data Stream</p>
          </div>
          <div className="flex items-center space-x-3">
             <div className="flex items-center space-x-1">
               <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
               <span className="text-[10px] font-bold text-gray-500">DOWN</span>
             </div>
             <div className="flex items-center space-x-1">
               <span className="w-2 h-2 bg-indigo-300 rounded-full"></span>
               <span className="text-[10px] font-bold text-gray-500">UP</span>
             </div>
          </div>
        </div>
        
        <div className="w-full -ml-4" style={{ height: 224 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorDown" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorUp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#818cf8" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f8fafc" />
              <XAxis dataKey="time" hide />
              <YAxis hide domain={[0, 'auto']} />
              <Tooltip 
                contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '12px' }}
                labelClassName="font-bold text-gray-400 mb-1"
              />
              <Area 
                type="monotone" 
                dataKey="down" 
                stroke="#3b82f6" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorDown)" 
                isAnimationActive={false}
              />
              <Area 
                type="monotone" 
                dataKey="up" 
                stroke="#818cf8" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorUp)" 
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Network Profile Information */}
      <div className="bg-white rounded-3xl border border-gray-100 p-6 space-y-5 shadow-sm">
        <div className="flex items-center space-x-2 mb-2">
           <Globe className="w-5 h-5 text-gray-900" />
           <h3 className="font-bold text-gray-900">Network Profile</h3>
        </div>
        
        <div className="flex items-center justify-between border-b border-gray-50 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-50 rounded-lg">
               <Wifi className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Current SSID</p>
              <p className="text-sm font-bold text-gray-900">{info.ssid}</p>
            </div>
          </div>
          <span className="bg-green-100 text-green-700 text-[9px] font-black px-2 py-0.5 rounded-full">CONNECTED</span>
        </div>

        <div className="flex items-center justify-between border-b border-gray-50 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-50 rounded-lg">
               <Globe className="w-4 h-4 text-indigo-600" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Public/Local IP</p>
              <p className="text-sm font-bold text-gray-900">{info.ip}</p>
            </div>
          </div>
          <span className="text-[10px] font-bold text-gray-400">Local Network</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gray-50 rounded-lg">
               <Activity className="w-4 h-4 text-gray-600" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Default Gateway</p>
              <p className="text-sm font-bold text-gray-900">{info.gateway}</p>
            </div>
          </div>
          <p className="text-[10px] font-bold text-gray-400">Scanning...</p>
        </div>
      </div>
    </div>
  );
};

export default NetworkStats;
