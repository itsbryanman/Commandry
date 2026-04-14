import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Plus, Activity } from 'lucide-react';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import { api, type Agent } from '../lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState({ agents_running: 0, agents_total: 0, mcp_servers: 0, today_cost_usd: 0 });
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.dashboardStats(), api.listAgents()])
      .then(([s, a]) => { setStats(s); setAgents(a); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <Link to="/agents" className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium" style={{ backgroundColor: 'var(--primary)', color: '#fff' }}>
            <Plus className="w-4 h-4" /> New Agent
          </Link>
          <Link to="/traces" className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm border" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
            <Activity className="w-4 h-4" /> View Traces
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Agents Running" value={stats.agents_running} sub={`${stats.agents_total} total`} color="var(--success)" />
        <StatCard label="Today's Cost" value={`$${stats.today_cost_usd.toFixed(2)}`} color="var(--warning)" />
        <StatCard label="MCP Servers" value={stats.mcp_servers} color="var(--accent)" />
        <StatCard label="System Load" value="—" sub="Host metrics coming soon" />
      </div>

      {/* Recent agents */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Agents</h2>
        {loading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Loading…</p>
        ) : agents.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No agents yet. Create one to get started.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((a) => (
              <Link
                key={a.id}
                to={`/agents/${a.id}`}
                className="rounded-lg p-4 border transition-colors"
                style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                    <span className="font-medium">{a.display_name}</span>
                  </div>
                  <StatusBadge status={a.status} />
                </div>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {a.model_provider}/{a.model_id}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
