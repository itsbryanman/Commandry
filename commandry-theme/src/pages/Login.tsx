import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Terminal } from 'lucide-react';
import { api } from '../lib/api';

export default function Login() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.login('admin', password);
      navigate('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="w-full max-w-sm p-8 rounded-xl border" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
        <div className="flex flex-col items-center mb-6">
          <Terminal className="w-10 h-10 mb-3" style={{ color: 'var(--primary)' }} />
          <h1 className="text-xl font-bold">Commandry</h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Mission control for your AI agents</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-md border text-sm outline-none"
              style={{ backgroundColor: 'var(--bg)', borderColor: 'var(--border)', color: 'var(--text)' }}
              placeholder="Enter admin password"
              autoFocus
            />
          </div>
          {error && <p className="text-xs" style={{ color: 'var(--danger)' }}>{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-md text-sm font-medium transition-opacity"
            style={{ backgroundColor: 'var(--primary)', color: '#fff', opacity: loading ? 0.6 : 1 }}
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
