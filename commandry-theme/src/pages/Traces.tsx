import { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api, type Trace } from '../lib/api';

export default function Traces() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listTraces().then(setTraces).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Execution Traces</h1>

      {loading ? (
        <p style={{ color: 'var(--text-secondary)' }}>Loading…</p>
      ) : traces.length === 0 ? (
        <div className="rounded-lg p-8 border text-center" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
          <Activity className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--primary)' }} />
          <p style={{ color: 'var(--text-secondary)' }}>No execution traces yet.</p>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ backgroundColor: 'var(--surface)' }}>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>ID</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Agent</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Trigger</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Status</th>
                <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Turns</th>
                <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Cost</th>
                <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Started</th>
              </tr>
            </thead>
            <tbody>
              {traces.map((t) => (
                <tr key={t.id} className="border-t" style={{ borderColor: 'var(--border)' }}>
                  <td className="px-4 py-3 font-mono text-xs">{t.id}</td>
                  <td className="px-4 py-3">{t.agent_id}</td>
                  <td className="px-4 py-3 text-xs">{t.triggered_by}</td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-3 text-right">{t.turns}</td>
                  <td className="px-4 py-3 text-right" style={{ color: 'var(--warning)' }}>${t.cost_usd.toFixed(4)}</td>
                  <td className="px-4 py-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {new Date(t.started_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
