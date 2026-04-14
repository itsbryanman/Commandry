import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Play, Square, RotateCw } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api, type Agent } from '../lib/api';

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getAgent(id).then(setAgent).catch(() => {}).finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <div className="p-6" style={{ color: 'var(--text-secondary)' }}>Loading…</div>;
  if (!agent) return <div className="p-6" style={{ color: 'var(--danger)' }}>Agent not found.</div>;

  const tabs = ['overview', 'configuration', 'prompt', 'budget'];

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    if (!id) return;
    const fn = action === 'start' ? api.startAgent : action === 'stop' ? api.stopAgent : api.startAgent;
    await fn(id);
    const updated = await api.getAgent(id);
    setAgent(updated);
  };

  return (
    <div className="p-6 space-y-6">
      <Link to="/agents" className="flex items-center gap-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
        <ArrowLeft className="w-4 h-4" /> Back to agents
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{agent.display_name}</h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>ID: {agent.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={agent.status} />
          <button onClick={() => handleAction('start')} className="p-2 rounded-md border" style={{ borderColor: 'var(--border)' }} title="Start">
            <Play className="w-4 h-4" style={{ color: 'var(--success)' }} />
          </button>
          <button onClick={() => handleAction('stop')} className="p-2 rounded-md border" style={{ borderColor: 'var(--border)' }} title="Stop">
            <Square className="w-4 h-4" style={{ color: 'var(--danger)' }} />
          </button>
          <button onClick={() => handleAction('restart')} className="p-2 rounded-md border" style={{ borderColor: 'var(--border)' }} title="Restart">
            <RotateCw className="w-4 h-4" style={{ color: 'var(--warning)' }} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: 'var(--border)' }}>
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="px-4 py-2 text-sm capitalize transition-colors"
            style={{
              color: tab === t ? 'var(--primary)' : 'var(--text-secondary)',
              borderBottom: tab === t ? '2px solid var(--primary)' : '2px solid transparent',
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="rounded-lg p-6 border" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
        {tab === 'overview' && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span style={{ color: 'var(--text-secondary)' }}>Runtime Type:</span> {agent.runtime_type}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Provider:</span> {agent.model_provider}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Model:</span> {agent.model_id}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Temperature:</span> {agent.model_temperature}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Max Tokens:</span> {agent.model_max_tokens}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Owner:</span> {agent.owner}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Created:</span> {new Date(agent.created_at).toLocaleString()}</div>
            <div><span style={{ color: 'var(--text-secondary)' }}>Updated:</span> {new Date(agent.updated_at).toLocaleString()}</div>
          </div>
        )}
        {tab === 'configuration' && (
          <div className="space-y-3 text-sm">
            <p style={{ color: 'var(--text-secondary)' }}>Configuration editing coming soon.</p>
            <pre className="p-3 rounded text-xs overflow-auto" style={{ backgroundColor: 'var(--bg)' }}>
              {JSON.stringify(agent, null, 2)}
            </pre>
          </div>
        )}
        {tab === 'prompt' && (
          <div className="space-y-3">
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Version: {agent.system_prompt_version || 1}
            </p>
            <pre className="p-4 rounded text-sm whitespace-pre-wrap" style={{ backgroundColor: 'var(--bg)' }}>
              {agent.system_prompt || 'No system prompt set.'}
            </pre>
          </div>
        )}
        {tab === 'budget' && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div><span style={{ color: 'var(--text-secondary)' }}>Daily Limit:</span> {agent.budget_daily_usd ? `$${agent.budget_daily_usd}` : 'None'}</div>
              <div><span style={{ color: 'var(--text-secondary)' }}>Monthly Limit:</span> {agent.budget_monthly_usd ? `$${agent.budget_monthly_usd}` : 'None'}</div>
              <div><span style={{ color: 'var(--text-secondary)' }}>Alert Threshold:</span> {agent.budget_alert_pct}%</div>
              <div><span style={{ color: 'var(--text-secondary)' }}>Auto-Kill:</span> {agent.budget_auto_kill ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
