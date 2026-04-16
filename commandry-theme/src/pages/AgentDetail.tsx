import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Play, Square, RotateCw, ShieldOff } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api, type Agent, type BudgetStatus } from '../lib/api';

function BudgetBar({ label, spend, limit, pct, state }: { label: string; spend: number; limit: number | null; pct: number; state: string }) {
  if (!limit) return null;
  const barColor = state === 'exceeded' ? 'var(--danger)' : state === 'critical' ? '#ef4444' : state === 'warning' ? 'var(--warning)' : 'var(--success)';
  const clampedPct = Math.min(pct, 100);

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium" style={{ color: barColor }}>
          ${spend.toFixed(2)} / ${limit.toFixed(2)} ({pct.toFixed(1)}%)
        </span>
      </div>
      <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
        <div
          className="h-2 rounded-full transition-all"
          style={{ width: `${clampedPct}%`, backgroundColor: barColor }}
        />
      </div>
      {state !== 'ok' && (
        <div className="flex items-center gap-1">
          <StatusBadge status={state} />
        </div>
      )}
    </div>
  );
}

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [budgetStatus, setBudgetStatus] = useState<BudgetStatus | null>(null);
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadAgent = () => {
    if (!id) return;
    Promise.all([api.getAgent(id), api.agentBudgetStatus(id)])
      .then(([a, bs]) => { setAgent(a); setBudgetStatus(bs); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadAgent(); }, [id]);

  if (loading) return <div className="p-6" style={{ color: 'var(--text-secondary)' }}>Loading...</div>;
  if (!agent) return <div className="p-6" style={{ color: 'var(--danger)' }}>Agent not found.</div>;

  const tabs = ['overview', 'configuration', 'prompt', 'budget'];

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    if (!id) return;
    setActionError(null);
    try {
      const fn = action === 'start' ? api.startAgent : action === 'stop' ? api.stopAgent : api.startAgent;
      await fn(id);
      loadAgent();
    } catch (err: any) {
      setActionError(err.message || 'Action failed');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Link to="/agents" className="flex items-center gap-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
        <ArrowLeft className="w-4 h-4" /> Back to agents
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            {agent.status === 'budget_blocked' && <ShieldOff className="w-6 h-6" style={{ color: 'var(--danger)' }} />}
            {agent.display_name}
          </h1>
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

      {actionError && (
        <div className="rounded-md p-3 text-sm" style={{ backgroundColor: '#ef444422', color: '#ef4444', border: '1px solid #ef444444' }}>
          {actionError}
        </div>
      )}

      {agent.status === 'budget_blocked' && (
        <div className="rounded-md p-3 text-sm" style={{ backgroundColor: '#f9731622', color: '#f97316', border: '1px solid #f9731644' }}>
          This agent is blocked due to budget overspend. It cannot execute new work until the budget period resets or limits are increased.
        </div>
      )}

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
          <div className="space-y-5">
            {/* Budget configuration */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span style={{ color: 'var(--text-secondary)' }}>Daily Limit:</span> {agent.budget_daily_usd ? `$${agent.budget_daily_usd}` : 'None'}</div>
              <div><span style={{ color: 'var(--text-secondary)' }}>Monthly Limit:</span> {agent.budget_monthly_usd ? `$${agent.budget_monthly_usd}` : 'None'}</div>
              <div><span style={{ color: 'var(--text-secondary)' }}>Alert Threshold:</span> {agent.budget_alert_pct}%</div>
              <div><span style={{ color: 'var(--text-secondary)' }}>Auto-Kill:</span> {agent.budget_auto_kill ? 'Yes' : 'No'}</div>
            </div>

            {/* Live spend bars */}
            {budgetStatus && (
              <div className="space-y-4 pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
                <h3 className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>Current Period Spend</h3>

                {budgetStatus.is_blocked && (
                  <div className="rounded-md p-2 text-xs font-medium" style={{ backgroundColor: '#f9731622', color: '#f97316' }}>
                    Agent is blocked by budget enforcement
                  </div>
                )}

                <BudgetBar
                  label="Daily"
                  spend={budgetStatus.daily_spend_usd}
                  limit={budgetStatus.daily_budget_usd}
                  pct={budgetStatus.daily_pct}
                  state={budgetStatus.daily_state}
                />
                <BudgetBar
                  label="Monthly"
                  spend={budgetStatus.monthly_spend_usd}
                  limit={budgetStatus.monthly_budget_usd}
                  pct={budgetStatus.monthly_pct}
                  state={budgetStatus.monthly_state}
                />

                {!budgetStatus.daily_budget_usd && !budgetStatus.monthly_budget_usd && (
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    No budget limits configured. Spend: ${budgetStatus.daily_spend_usd.toFixed(2)} today, ${budgetStatus.monthly_spend_usd.toFixed(2)} this month.
                  </p>
                )}
              </div>
            )}

            {/* Recent alerts */}
            {budgetStatus && budgetStatus.recent_alerts.length > 0 && (
              <div className="space-y-2 pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
                <h3 className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>Recent Alerts</h3>
                <div className="space-y-1">
                  {budgetStatus.recent_alerts.map((a) => (
                    <div key={a.id} className="flex items-center justify-between text-xs p-2 rounded" style={{ backgroundColor: 'var(--bg)' }}>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={a.alert_type} />
                        <span className="capitalize">{a.budget_type}</span>
                        <span style={{ color: 'var(--text-secondary)' }}>{a.period_key}</span>
                      </div>
                      <span style={{ color: 'var(--danger)' }}>${a.actual_usd?.toFixed(2)} / ${a.limit_usd?.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
