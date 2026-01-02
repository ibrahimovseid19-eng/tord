
import React from 'react';
import { 
  Router, 
  Smartphone, 
  Monitor, 
  Laptop, 
  Cpu, 
  Printer,
  Wifi,
  ShieldCheck,
  Terminal as TerminalIcon,
  Activity,
  Radar
} from 'lucide-react';
import { Device } from './types';

export const INITIAL_DEVICES: Device[] = [
  { id: '1', name: 'Main Router (Gateway)', ip: '192.168.1.1', mac: 'BC:62:0E:12:35:01', vendor: 'TP-Link', type: 'router', status: 'online', lastSeen: 'Now', os: 'Proprietary Linux' },
  { id: '2', name: 'iPhone 15 Pro', ip: '192.168.1.15', mac: '44:F0:22:B1:3D:A1', vendor: 'Apple Inc.', type: 'phone', status: 'online', lastSeen: 'Now', os: 'iOS 17.4.1' },
  { id: '3', name: 'Workstation-X', ip: '192.168.1.102', mac: '98:B9:59:6E:AF:83', vendor: 'Dell', type: 'desktop', status: 'online', lastSeen: '2 mins ago', os: 'Windows 11 Pro' },
  { id: '4', name: 'MacBook Air', ip: '192.168.1.105', mac: 'BC:62:0E:12:35:04', vendor: 'Apple Inc.', type: 'laptop', status: 'offline', lastSeen: '1 hour ago', os: 'macOS Sonoma' },
  { id: '5', name: 'Smart Bulb 01', ip: '192.168.1.20', mac: '52:54:00:12:35:02', vendor: 'Tuya Smart', type: 'iot', status: 'online', lastSeen: 'Now', os: 'Embedded RTOS' },
  { id: '6', name: 'HP LaserJet Pro', ip: '192.168.1.150', mac: '12:34:56:78:90:AB', vendor: 'HP', type: 'printer', status: 'online', lastSeen: 'Now', os: 'HP FutureSmart' },
];

export const DEVICE_ICONS = {
  router: <Router className="w-5 h-5" />,
  phone: <Smartphone className="w-5 h-5" />,
  desktop: <Monitor className="w-5 h-5" />,
  laptop: <Laptop className="w-5 h-5" />,
  iot: <Cpu className="w-5 h-5" />,
  printer: <Printer className="w-5 h-5" />,
};

export const NAV_ITEMS = [
  { id: 'devices', label: 'Devices', icon: <Wifi className="w-5 h-5" />, path: '/' },
  { id: 'network', label: 'Network', icon: <Activity className="w-5 h-5" />, path: '/network' },
  { id: 'security', label: 'Security', icon: <ShieldCheck className="w-5 h-5" />, path: '/security' },
  { id: 'terminal', label: 'Terminal', icon: <TerminalIcon className="w-5 h-5" />, path: '/terminal' },
];
