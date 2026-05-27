'use client';

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface YieldCurveChartProps {
  data: { maturity: string; yield: number }[];
  height?: number;
}

export default function YieldCurveChart({ data, height = 300 }: YieldCurveChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
        <XAxis dataKey="maturity" tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} />
        <YAxis tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} domain={['auto', 'auto']} tickFormatter={(v: number) => `${v.toFixed(1)}%`} />
        <Tooltip
          contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #334155', borderRadius: '8px', color: '#F8FAFC', fontSize: '12px' }}
          formatter={(value: number) => [`${value.toFixed(3)}%`, 'Yield']}
          labelStyle={{ color: '#38BDF8', fontWeight: 600 }}
        />
        <Area type="monotone" dataKey="yield" stroke="#2563EB" strokeWidth={2} fill="url(#yieldGradient)" dot={{ fill: '#2563EB', r: 4, strokeWidth: 0 }} activeDot={{ r: 6, fill: '#38BDF8', stroke: '#2563EB', strokeWidth: 2 }} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
