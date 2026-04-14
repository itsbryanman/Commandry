import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  DollarSign,
  Server,
  FileText,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Terminal,
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Agents', path: '/agents', icon: Bot },
  { label: 'Tokens & Cost', path: '/cost', icon: DollarSign },
  { label: 'MCP Servers', path: '/mcp-servers', icon: Server },
  { label: 'Prompts', path: '/prompts', icon: FileText },
  { label: 'Traces', path: '/traces', icon: Activity },
  { type: 'divider' as const },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex flex-col h-screen sticky top-0 transition-all duration-200 border-r ${
        collapsed ? 'w-16' : 'w-60'
      }`}
      style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 h-14 border-b" style={{ borderColor: 'var(--border)' }}>
        <Terminal className="w-6 h-6 flex-shrink-0" style={{ color: 'var(--primary)' }} />
        {!collapsed && <span className="text-lg font-bold tracking-tight">Commandry</span>}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {NAV_ITEMS.map((item, i) => {
          if ('type' in item && item.type === 'divider') {
            return <hr key={i} className="my-2 mx-3" style={{ borderColor: 'var(--border)' }} />;
          }
          const Icon = item.icon!;
          const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path!));
          return (
            <Link
              key={item.path}
              to={item.path!}
              className={`flex items-center gap-3 px-4 py-2 mx-2 rounded-md text-sm transition-colors ${
                active ? 'font-medium' : ''
              }`}
              style={{
                backgroundColor: active ? 'var(--surface-hover)' : 'transparent',
                color: active ? 'var(--text)' : 'var(--text-secondary)',
              }}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-10 border-t transition-colors cursor-pointer"
        style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </aside>
  );
}
