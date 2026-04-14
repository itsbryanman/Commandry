import { Settings as SettingsIcon } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="rounded-lg p-8 border text-center" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
        <SettingsIcon className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--primary)' }} />
        <h2 className="text-lg font-semibold mb-2">Commandry Settings</h2>
        <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
          Global configuration, API keys, and preferences.
        </p>
        <div className="text-left max-w-md mx-auto space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b" style={{ borderColor: 'var(--border)' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Version</span>
            <span className="font-mono">0.1.0</span>
          </div>
          <div className="flex justify-between py-2 border-b" style={{ borderColor: 'var(--border)' }}>
            <span style={{ color: 'var(--text-secondary)' }}>API Port</span>
            <span className="font-mono">10000</span>
          </div>
          <div className="flex justify-between py-2 border-b" style={{ borderColor: 'var(--border)' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Database</span>
            <span className="font-mono">SQLite</span>
          </div>
          <div className="flex justify-between py-2 border-b" style={{ borderColor: 'var(--border)' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Theme</span>
            <span>Dark</span>
          </div>
        </div>
      </div>
    </div>
  );
}
