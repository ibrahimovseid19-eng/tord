
import React from 'react';
import { ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Device } from '../types';
import { DEVICE_ICONS } from '../constants';

interface DeviceItemProps {
  device: Device;
}

const DeviceItem: React.FC<DeviceItemProps> = ({ device }) => {
  const navigate = useNavigate();

  return (
    <div 
      onClick={() => navigate(`/device/${device.id}`)}
      className="flex items-center justify-between p-4 bg-white border-b border-gray-100 active:bg-gray-50 transition-colors cursor-pointer group"
    >
      <div className="flex items-center space-x-4">
        <div className={`p-2 rounded-xl transition-all ${device.status === 'online' ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
          {DEVICE_ICONS[device.type]}
        </div>
        <div>
          <h3 className={`font-semibold text-sm ${device.status === 'offline' ? 'text-gray-400' : 'text-gray-900'}`}>
            {device.name}
          </h3>
          <div className="flex items-center space-x-2 text-[10px] text-gray-500 mt-0.5 font-medium tabular-nums">
            <span>{device.ip}</span>
            <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
            <span>{device.mac}</span>
          </div>
          <p className="text-[10px] text-gray-400 uppercase font-bold tracking-tighter mt-1">{device.vendor}</p>
        </div>
      </div>
      
      <div className="flex flex-col items-end space-y-1">
        {device.status === 'online' ? (
          <div className="flex items-center space-x-1 bg-green-50 px-2 py-0.5 rounded-full">
             <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
             <span className="text-[9px] font-black text-green-600 uppercase">Live</span>
          </div>
        ) : (
          <span className="text-[9px] font-bold text-gray-400">{device.lastSeen ? `Seen: ${device.lastSeen.split(' ')[1]}` : 'Offline'}</span>
        )}
        <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors" />
      </div>
    </div>
  );
};

export default DeviceItem;
