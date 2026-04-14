import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-6">
      <h1 className="text-6xl font-bold mb-4" style={{ color: 'var(--primary)' }}>404</h1>
      <p className="text-lg mb-6" style={{ color: 'var(--text-secondary)' }}>Page not found</p>
      <Link
        to="/"
        className="px-4 py-2 rounded-md text-sm font-medium"
        style={{ backgroundColor: 'var(--primary)', color: '#fff' }}
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
