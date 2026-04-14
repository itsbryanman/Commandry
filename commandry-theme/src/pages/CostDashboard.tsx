import { useEffect, useState } from 'react';
import StatCard from '../components/StatCard';
import { api, type TokenByModel } from '../lib/api';

export default function CostDashboard() {
  const [summary, setSummary] = useState({ today_usd: 0, month_usd: 0, total_usd: 0 });
  const [byModel, setByModel] = useState<TokenByModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.tokenSummary(), api.tokensByModel()])
      .then(([s, m]) => { setSummary(s); setByModel(m); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Tokens &amp; Cost</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Today's Spend" value={`$${summary.today_usd.toFixed(2)}`} color="var(--warning)" />
        <StatCard label="This Month" value={`$${summary.month_usd.toFixed(2)}`} color="var(--accent)" />
        <StatCard label="All Time" value={`$${summary.total_usd.toFixed(2)}`} color="var(--text)" />
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Cost by Model</h2>
        {loading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Loading…</p>
        ) : byModel.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No token usage recorded yet.</p>
        ) : (
          <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ backgroundColor: 'var(--surface)' }}>
                  <th className="text-left px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Model</th>
                  <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Input Tokens</th>
                  <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Output Tokens</th>
                  <th className="text-right px-4 py-3 font-medium" style={{ color: 'var(--text-secondary)' }}>Total Cost</th>
                </tr>
              </thead>
              <tbody>
                {byModel.map((m) => (
                  <tr key={m.model_id} className="border-t" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-4 py-3 font-mono text-xs">{m.model_id}</td>
                    <td className="px-4 py-3 text-right">{m.total_input.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">{m.total_output.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right font-medium" style={{ color: 'var(--warning)' }}>${m.total_cost.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
