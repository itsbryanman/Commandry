interface Props {
  status: string;
}

const COLORS: Record<string, { bg: string; text: string }> = {
  running: { bg: '#22c55e22', text: '#22c55e' },
  idle: { bg: '#6366f122', text: '#6366f1' },
  errored: { bg: '#ef444422', text: '#ef4444' },
  stopped: { bg: '#94a3b822', text: '#94a3b8' },
  queued: { bg: '#f59e0b22', text: '#f59e0b' },
  ok: { bg: '#22c55e22', text: '#22c55e' },
  unknown: { bg: '#94a3b822', text: '#94a3b8' },
  completed: { bg: '#22c55e22', text: '#22c55e' },
  failed: { bg: '#ef444422', text: '#ef4444' },
};

export default function StatusBadge({ status }: Props) {
  const c = COLORS[status] || COLORS.unknown;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
      style={{ backgroundColor: c.bg, color: c.text }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full mr-1.5"
        style={{ backgroundColor: c.text }}
      />
      {status}
    </span>
  );
}
