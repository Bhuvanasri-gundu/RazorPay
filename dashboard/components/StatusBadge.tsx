import React from 'react';
import { cn } from '@/lib/utils';

export interface StatusBadgeProps {
  status: string;
  className?: string;
}

const statusColorMap: Record<string, string> = {
  RECOVERED: 'bg-green-500/10 text-green-400 border-green-500/20',
  OPEN: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  ANALYZING: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  ACTION_PENDING: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  IN_PROGRESS: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  STOPPED: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  STOPPED_BY_POLICY: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  REQUIRES_HUMAN_APPROVAL: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  RECOVERY_FAILED: 'bg-red-500/10 text-red-400 border-red-500/20',
  ESCALATED: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const styles = statusColorMap[status] || 'bg-zinc-800 text-zinc-300 border-zinc-700';
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border tracking-wide uppercase',
        styles,
        className
      )}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
};
