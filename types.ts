
export interface Device {
  id: string;
  name: string;
  ip: string;
  mac: string;
  vendor: string;
  type: 'router' | 'phone' | 'desktop' | 'laptop' | 'iot' | 'printer';
  status: 'online' | 'offline';
  lastSeen: string;
  os?: string;
}

export enum TabType {
  DEVICES = 'devices',
  NETWORK = 'network',
  TERMINAL = 'terminal',
  SECURITY = 'security'
}

export interface TerminalLine {
  text: string;
  type: 'command' | 'output' | 'error' | 'success' | 'info';
}
