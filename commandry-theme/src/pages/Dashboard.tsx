import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Plus, Activity, AlertTriangle, ShieldOff } from 'lucide-react';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import { api, type Agent, type BudgetAlert, type DashboardStats } from '../lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    agents_running: 0, agents_total: 0, agents_blocked: 0, mcp_servers: 0, today_cost_usd: 0, active_alerts: 0,
  });
  const [agents, setAgents] = useState<Agent[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.dashboardStats(), api.listAgents(), api.dashboardAlerts()])
      .then(([s, a, al]) => { setStats(s); setAgents(a); setAlerts(al); })
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
        <StatCard label="Budget Alerts" value={stats.active_alerts} sub={stats.agents_blocked > 0 ? `${stats.agents_blocked} blocked` : 'None blocked'} color={stats.active_alerts > 0 ? 'var(--danger)' : 'var(--success)'} />
        <StatCard label="MCP Servers" value={stats.mcp_servers} color="var(--accent)" />
      </div>

      {/* Budget alerts */}
      {alerts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" style={{ color: 'var(--warning)' }} />
            Recent Budget Alerts
          </h2>
          <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ backgroundColor: 'var(--surface)' }}>
                  <th className="text-left px-4 py-2 font-medium" style={{ color: 'var(--text-secondary)' }}>Agent</th>
                  <th className="text-left px-4 py-2 font-medium" style={{ color: 'var(--text-secondary)' }}>Level</th>
                  <th className="text-left px-4 py-2 font-medium" style={{ color: 'var(--text-secondary)' }}>Budget</th>
                  <th className="text-right px-4 py-2 font-medium" style={{ color: 'var(--text-secondary)' }}>Limit</th>
                  <th className="text-right px-4 py-2 font-medium" style={{ color: 'var(--text-secondary)' }}>Actual</th>
                  <th className="text-left px-4 py-2 font-medium" style={{ color: 'var(--text-secondary)' }}>When</th>
                </tr>
              </thead>
              <tbody>
                {alerts.slice(0, 10).map((a) => (
                  <tr key={a.id} className="border-t" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-4 py-2">
                      <Link to={`/agents/${a.agent_id}`} className="hover:underline" style={{ color: 'var(--primary)' }}>
                        {a.agent_id}
                      </Link>
                    </td>
                    <td className="px-4 py-2"><StatusBadge status={a.alert_type} /></td>
                    <td className="px-4 py-2 capitalize">{a.budget_type}</td>
                    <td className="px-4 py-2 text-right">${a.limit_usd?.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right font-medium" style={{ color: 'var(--danger)' }}>${a.actual_usd?.toFixed(2)}</td>
                    <td className="px-4 py-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                      {a.triggered_at ? new Date(a.triggered_at).toLocaleString() : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Agents grid */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Agents</h2>
        {loading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Loading...</p>
        ) : agents.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No agents yet. Create one to get started.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((a) => (
              <Link
                key={a.id}
                to={`/agents/${a.id}`}
                className="rounded-lg p-4 border transition-colors"
                style={{ backgroundColor: 'var(--surface)', borderColor: a.status === 'budget_blocked' ? 'var(--danger)' : 'var(--border)' }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {a.status === 'budget_blocked' ? (
                      <ShieldOff className="w-5 h-5" style={{ color: 'var(--danger)' }} />
                    ) : (
                      <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                    )}
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
