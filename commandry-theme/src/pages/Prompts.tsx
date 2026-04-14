import { FileText } from 'lucide-react';

export default function Prompts() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Prompts</h1>
      <div className="rounded-lg p-8 border text-center" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}>
        <FileText className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--primary)' }} />
        <h2 className="text-lg font-semibold mb-2">Prompt Version Control</h2>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Git-style versioning for agent system prompts. Select an agent from the Agents page to view and edit prompts with diff history.
        </p>
      </div>
    </div>
  );
}
