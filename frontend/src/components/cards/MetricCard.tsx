'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number | null;
  change?: number;
  unit?: string;
  icon?: React.ReactNode;
  accentColor?: string;
}

export default function MetricCard({ label, value, change, unit = '%', icon, accentColor = 'text-accent' }: MetricCardProps) {
  const isPositive = (change ?? 0) > 0;
  const isNegative = (change ?? 0) < 0;

  return (
    <div className="panel card-hover p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className={`text-xs font-semibold uppercase tracking-wider ${accentColor}`}>{label}</span>
        {icon && <div className="text-text-tertiary">{icon}</div>}
      </div>
      <div className="flex items-end gap-2">
        <span className="metric-value text-text">
          {value !== null && value !== undefined ? value : '—'}
          {value !== null && <span className="text-base font-normal text-text-secondary ml-0.5">{unit}</span>}
        </span>
      </div>
      {change !== undefined && (
        <div className={`flex items-center gap-1 text-xs font-mono ${isPositive ? 'text-positive' : isNegative ? 'text-negative' : 'text-text-tertiary'}`}>
          {isPositive ? <TrendingUp className="w-3 h-3" /> : isNegative ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          <span>{isPositive ? '+' : ''}{change?.toFixed(3)}</span>
        </div>
      )}
    </div>
  );
}
