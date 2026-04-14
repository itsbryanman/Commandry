export default function TopBar() {
  return (
    <header
      className="flex items-center justify-between px-6 h-14 border-b"
      style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      <div className="flex items-center gap-2">
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Mission control for your AI agents
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--accent)' }}>
          v0.1.0
        </span>
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>admin</span>
      </div>
    </header>
  );
}
