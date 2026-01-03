
import React, { useState, useRef, useEffect } from 'react';
import { TerminalLine } from '../types';
import { INITIAL_DEVICES } from '../constants';

interface TerminalComponentProps {
  initialLines?: TerminalLine[];
  apiUrl: string;
}

const TerminalComponent: React.FC<TerminalComponentProps> = ({ initialLines = [], apiUrl }) => {
  const [history, setHistory] = useState<TerminalLine[]>(initialLines);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const fullInput = input.trim();
    const parts = fullInput.split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    // Initial echo
    setHistory(prev => [...prev, { text: `root@netguardian:~$ ${fullInput}`, type: 'command' }]);
    setInput('');

    // Client-side commands
    if (command === 'clear') {
      setHistory([]);
      return;
    }

    if (command === 'help') {
      const helpLines: TerminalLine[] = [
        { text: 'Available Real Commands (Python Kernel):', type: 'info' },
        { text: '  scan            - Discover devices on network', type: 'output' },
        { text: '  ping [ip]       - ICMP Ping', type: 'output' },
        { text: '  trace [ip]      - Traceroute to target', type: 'output' },
        { text: '  ports [ip]      - Scan common open ports', type: 'output' },
        { text: '  ifconfig / ipa  - Show network interfaces', type: 'output' },
        { text: '  netstat         - Show active connections', type: 'output' },
        { text: '  nslookup [host] - DNS Resolution', type: 'output' },
        { text: '  wifi_keys       - Show saved Wi-Fi passwords', type: 'output' },
        { text: '  geoip [ip]      - Geolocate an IP address', type: 'output' },
        { text: '  whois [domain]  - Domain registration info', type: 'output' },
        { text: '  headers [url]   - Analyze HTTP security headers', type: 'output' },
        { text: '  system          - System Information', type: 'output' },
        { text: '  clear           - Clear screen', type: 'output' },
      ];
      setHistory(prev => [...prev, ...helpLines]);
      return;
    }

    // Backend commands
    try {
      setHistory(prev => [...prev, { text: 'Executing...', type: 'info' }]);
      
      const res = await fetch(`${apiUrl}/api/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, args })
      });
      
      const data = await res.json();
      
      setHistory(prev => {
        // Remove "Executing..."
        const clean = prev.slice(0, -1);
        return [...clean, { text: data.output || 'No output.', type: data.type === 'error' ? 'error' : 'output' }];
      });
      
    } catch (err) {
      setHistory(prev => [
        ...prev.slice(0, -1), // remove executing
        { text: 'Connection to backend failed.', type: 'error' }
      ]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-emerald-500 terminal-font p-4 overflow-hidden shadow-inner">
      <div className="flex-1 overflow-y-auto space-y-1 mb-4">
        {history.map((line, idx) => (
          <div key={idx} className={`text-xs break-all whitespace-pre-wrap font-mono leading-relaxed ${
            line.type === 'error' ? 'text-red-400' : 
            line.type === 'success' ? 'text-green-400 font-bold' : 
            line.type === 'info' ? 'text-blue-400' : 
            line.type === 'command' ? 'text-white font-bold mt-2' : 'text-emerald-500'
          }`}>
            {line.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      
      <form onSubmit={handleCommand} className="flex items-center border-t border-slate-800 pt-3 pb-2">
        <span className="text-white mr-2 shrink-0 text-xs opacity-70">#</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="bg-transparent border-none outline-none flex-1 text-sm text-white placeholder-slate-700"
          placeholder="Enter command..."
          autoFocus
          spellCheck={false}
          autoComplete="off"
        />
      </form>
    </div>
  );
};

export default TerminalComponent;
