interface Props {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

export default function StatCard({ label, value, sub, color }: Props) {
  return (
    <div
      className="rounded-lg p-5 border"
      style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      <p className="text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--text-secondary)' }}>
        {label}
      </p>
      <p className="text-2xl font-bold" style={{ color: color || 'var(--text)' }}>
        {value}
      </p>
      {sub && (
        <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
          {sub}
        </p>
      )}
    </div>
  );
}
