'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number | null;
  change?: number;
  unit?: string;
  icon?: React.ReactNode;
  accentColor?: string;
  prefix?: string;
  description?: string;
  loading?: boolean;
  error?: string;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export default function MetricCard({
  label,
  value,
  change,
  unit = '%',
  icon,
  accentColor = 'text-accent',
  prefix,
  description,
  loading,
  error,
  size = 'md',
  onClick
}: MetricCardProps) {
  const isPositive = (change ?? 0) > 0;
  const isNegative = (change ?? 0) < 0;

  if (loading) {
    return (
      <div className="panel card-hover p-4 flex flex-col gap-1 animate-pulse">
        <div className="h-4 w-24 bg-slate-700 rounded mb-2"></div>
        <div className="h-8 w-16 bg-slate-700 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel p-4 flex flex-col gap-1 border-negative/50 bg-negative/5">
        <span className="text-xs font-semibold uppercase tracking-wider text-negative">{label}</span>
        <span className="text-sm text-text-secondary mt-1">{error}</span>
      </div>
    );
  }

  return (
    <div 
      className={`panel card-hover p-4 flex flex-col gap-1 ${onClick ? 'cursor-pointer' : ''} ${size === 'sm' ? 'scale-90' : size === 'lg' ? 'scale-110' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <span className={`text-xs font-semibold uppercase tracking-wider ${accentColor}`}>{label}</span>
        {icon && <div className="text-text-tertiary">{icon}</div>}
      </div>
      <div className="flex items-end gap-2">
        <span className="metric-value text-text">
          {prefix}{value !== null && value !== undefined ? value : '—'}
          {value !== null && <span className="text-base font-normal text-text-secondary ml-0.5">{unit}</span>}
        </span>
      </div>
      {change !== undefined && (
        <div className={`flex items-center gap-1 text-xs font-mono ${isPositive ? 'text-positive' : isNegative ? 'text-negative' : 'text-text-tertiary'}`}>
          {isPositive ? <TrendingUp className="w-3 h-3" /> : isNegative ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          <span>{isPositive ? '+' : ''}{change?.toFixed(3)}</span>
        </div>
      )}
      {description && <p className="text-[10px] text-text-tertiary mt-1 italic">{description}</p>}
    </div>
  );
}
