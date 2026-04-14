import { useEffect, useState } from 'react';
import { Server } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api, type MCPServer } from '../lib/api';

export default function MCPServers() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listMCPServers().then(setServers).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">MCP Servers</h1>
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium" style={{ backgroundColor: 'var(--primary)', color: '#fff' }}>
          Add MCP Server
        </button>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-secondary)' }}>Loading…</p>
      ) : servers.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)' }}>No MCP servers registered.</p>
      ) : (
        <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ backgroundColor: 'var(--surface)' }}>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Name</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Transport</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Status</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Tools</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {servers.map((s) => {
                const tools = s.tools_cached ? JSON.parse(s.tools_cached) : [];
                return (
                  <tr key={s.id} className="border-t" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Server className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                        <div>
                          <p className="font-medium">{s.display_name}</p>
                          <p className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{s.id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{s.transport}</td>
                    <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--text-secondary)' }}>{tools.length} tools</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {s.status !== 'running' && (
                          <button onClick={() => api.startMCPServer(s.id).then(() => api.listMCPServers().then(setServers))} className="px-2 py-1 text-xs rounded" style={{ backgroundColor: 'var(--success)', color: '#fff' }}>Start</button>
                        )}
                        {s.status === 'running' && (
                          <button onClick={() => api.stopMCPServer(s.id).then(() => api.listMCPServers().then(setServers))} className="px-2 py-1 text-xs rounded" style={{ backgroundColor: 'var(--danger)', color: '#fff' }}>Stop</button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
