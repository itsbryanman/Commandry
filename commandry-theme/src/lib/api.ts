const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(body.error || body.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  // Health
  health: () => request<{ status: string }>('/health'),

  // Dashboard
  dashboardStats: () =>
    request<DashboardStats>('/dashboard/stats'),
  dashboardAlerts: () => request<BudgetAlert[]>('/dashboard/alerts'),

  // Agents
  listAgents: () => request<Agent[]>('/agents'),
  getAgent: (id: string) => request<Agent>(`/agents/${id}`),
  createAgent: (data: Partial<Agent>) => request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  updateAgent: (id: string, data: Partial<Agent>) =>
    request<Agent>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAgent: (id: string) => request<{ ok: boolean }>(`/agents/${id}`, { method: 'DELETE' }),
  startAgent: (id: string) => request<{ ok: boolean }>(`/agents/${id}/start`, { method: 'POST' }),
  stopAgent: (id: string) => request<{ ok: boolean }>(`/agents/${id}/stop`, { method: 'POST' }),

  // Tokens
  tokenSummary: () => request<{ today_usd: number; month_usd: number; total_usd: number }>('/tokens/summary'),
  tokensByModel: () => request<TokenByModel[]>('/tokens/by-model'),
  tokensByAgent: (id: string) => request<TokenRecord[]>(`/tokens/by-agent/${id}`),

  // Pricing
  listPricing: () => request<Pricing[]>('/pricing'),

  // MCP Servers
  listMCPServers: () => request<MCPServer[]>('/mcp-servers'),
  getMCPServer: (id: string) => request<MCPServer>(`/mcp-servers/${id}`),
  startMCPServer: (id: string) => request<{ ok: boolean }>(`/mcp-servers/${id}/start`, { method: 'POST' }),
  stopMCPServer: (id: string) => request<{ ok: boolean }>(`/mcp-servers/${id}/stop`, { method: 'POST' }),

  // Traces
  listTraces: (agentId?: string) => request<Trace[]>(`/traces${agentId ? `?agent_id=${agentId}` : ''}`),

  // Prompts
  listPrompts: (agentId: string) => request<PromptVersion[]>(`/prompts/${agentId}`),

  // Budget alerts & status
  listAlerts: () => request<BudgetAlert[]>('/budget/alerts'),
  ackAlert: (id: number) => request<{ ok: boolean }>(`/budget/alerts/${id}/ack`, { method: 'POST' }),
  agentBudgetStatus: (agentId: string) => request<BudgetStatus>(`/budget/status/${agentId}`),

  // Auth
  login: (username: string, password: string) =>
    request<{ ok: boolean }>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
};

// Types
export interface Agent {
  id: string;
  display_name: string;
  owner: string;
  status: string;
  runtime_type: string;
  model_provider: string;
  model_id: string;
  model_temperature: number;
  model_max_tokens: number;
  system_prompt: string | null;
  budget_daily_usd: number | null;
  budget_monthly_usd: number | null;
  budget_alert_pct: number;
  budget_auto_kill: boolean;
  system_prompt_version: number;
  created_at: string;
  updated_at: string;
}

export interface MCPServer {
  id: string;
  display_name: string;
  transport: string;
  command: string | null;
  url: string | null;
  status: string;
  tools_cached: string | null;
  last_health_check: string | null;
  last_health_status: string | null;
  created_at: string;
}

export interface Trace {
  id: string;
  agent_id: string;
  triggered_by: string;
  started_at: string;
  ended_at: string | null;
  status: string;
  turns: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface TokenByModel {
  model_id: string;
  total_input: number;
  total_output: number;
  total_cost: number;
}

export interface TokenRecord {
  id: number;
  timestamp: string;
  model_id: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface Pricing {
  id: number;
  provider: string;
  model_id: string;
  input_price_per_mtok: number;
  output_price_per_mtok: number;
  effective_date: string;
}

export interface PromptVersion {
  id: number;
  version: number;
  tag: string | null;
  content: string;
  created_at: string;
  created_by: string;
}

export interface BudgetAlert {
  id: number;
  agent_id: string;
  alert_type: string;
  budget_type: string;
  period_key: string;
  limit_usd: number;
  actual_usd: number;
  triggered_at: string;
  acknowledged: boolean;
}

export interface BudgetStatus {
  daily_spend_usd: number;
  monthly_spend_usd: number;
  daily_budget_usd: number | null;
  monthly_budget_usd: number | null;
  daily_pct: number;
  monthly_pct: number;
  daily_state: string;
  monthly_state: string;
  budget_alert_pct: number;
  budget_auto_kill: boolean;
  is_blocked: boolean;
  recent_alerts: BudgetAlert[];
}

export interface DashboardStats {
  agents_running: number;
  agents_total: number;
  agents_blocked: number;
  mcp_servers: number;
  today_cost_usd: number;
  active_alerts: number;
}
