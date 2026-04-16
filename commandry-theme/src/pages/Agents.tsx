import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Plus, ShieldOff } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api, type Agent } from '../lib/api';

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listAgents().then(setAgents).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Agents</h1>
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium"
          style={{ backgroundColor: 'var(--primary)', color: '#fff' }}
        >
          <Plus className="w-4 h-4" /> New Agent
        </button>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-secondary)' }}>Loading…</p>
      ) : agents.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)' }}>No agents registered yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((a) => (
            <Link
              key={a.id}
              to={`/agents/${a.id}`}
              className="rounded-lg p-5 border transition-colors hover:border-[var(--primary)]"
              style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {a.status === 'budget_blocked' ? (
                    <ShieldOff className="w-5 h-5" style={{ color: 'var(--danger)' }} />
                  ) : (
                    <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                  )}
                  <span className="font-semibold">{a.display_name}</span>
                </div>
                <StatusBadge status={a.status} />
              </div>
              <div className="space-y-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                <p>Model: {a.model_id}</p>
                <p>Provider: {a.model_provider}</p>
                <p>Owner: {a.owner}</p>
                {a.budget_daily_usd && <p>Budget: ${a.budget_daily_usd}/day</p>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
