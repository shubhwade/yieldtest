'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Globe, TrendingUp, TrendingDown } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const MOCK_INDICATORS = [
  { name: 'Fed Funds Rate', value: 5.33, change: 0, unit: '%', category: 'rates', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 5.33 - (11-i)*0.02 })) },
  { name: 'SOFR', value: 5.31, change: -0.01, unit: '%', category: 'rates', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 5.31 - (11-i)*0.015 })) },
  { name: 'CPI YoY', value: 3.2, change: -0.1, unit: '%', category: 'inflation', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 3.2 + (11-i)*0.08 })) },
  { name: 'Core CPI', value: 3.6, change: -0.1, unit: '%', category: 'inflation', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 3.6 + (11-i)*0.05 })) },
  { name: 'PCE Price Index', value: 2.7, change: -0.1, unit: '%', category: 'inflation', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 2.7 + (11-i)*0.06 })) },
  { name: 'Unemployment', value: 3.8, change: 0.1, unit: '%', category: 'employment', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 3.8 - (11-i)*0.02 })) },
  { name: '30Y Mortgage', value: 6.89, change: -0.02, unit: '%', category: 'rates', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 6.89 + (11-i)*0.05 })) },
  { name: '5Y Breakeven', value: 2.35, change: 0.02, unit: '%', category: 'inflation', history: Array.from({length: 12}, (_, i) => ({ month: `${i+1}`, value: 2.35 - (11-i)*0.01 })) },
];

const EVENTS = [
  { date: 'Jun 5', event: 'FOMC Meeting Minutes', impact: 'high' },
  { date: 'Jun 7', event: 'Employment Report', impact: 'high' },
  { date: 'Jun 12', event: 'CPI Release', impact: 'high' },
  { date: 'Jun 14', event: 'PPI Release', impact: 'medium' },
  { date: 'Jun 18', event: 'FOMC Rate Decision', impact: 'high' },
  { date: 'Jun 21', event: 'PCE Price Index', impact: 'medium' },
];

export default function MacroPage() {
  const [selectedIndicator, setSelectedIndicator] = useState(MOCK_INDICATORS[0]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <h1 className="text-lg font-bold">Macro Dashboard</h1>

      {/* Indicator Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {MOCK_INDICATORS.map((ind, i) => (
          <button key={i} onClick={() => setSelectedIndicator(ind)} className={`panel p-3 card-hover text-left ${selectedIndicator.name === ind.name ? 'border-accent/50' : ''}`}>
            <div className="text-[10px] text-text-secondary uppercase tracking-wider">{ind.name}</div>
            <div className="font-mono text-xl font-bold mt-1">{ind.value.toFixed(2)}{ind.unit}</div>
            <div className={`flex items-center gap-1 text-xs font-mono mt-1 ${ind.change > 0 ? 'text-positive' : ind.change < 0 ? 'text-negative' : 'text-text-tertiary'}`}>
              {ind.change > 0 ? <TrendingUp className="w-3 h-3" /> : ind.change < 0 ? <TrendingDown className="w-3 h-3" /> : null}
              {ind.change > 0 ? '+' : ''}{ind.change.toFixed(2)}
            </div>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chart */}
        <div className="panel lg:col-span-2">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold">{selectedIndicator.name} — 12 Month Trend</span>
            </div>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={selectedIndicator.history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} />
                <YAxis tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} domain={['auto', 'auto']} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#F8FAFC', fontSize: 12 }} />
                <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2} dot={{ fill: '#2563EB', r: 3 }} name={selectedIndicator.name} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Economic Calendar */}
        <div className="panel">
          <div className="panel-header"><div className="flex items-center gap-2"><Globe className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">Economic Calendar</span></div></div>
          <div className="divide-y divide-border/50">
            {EVENTS.map((e, i) => (
              <div key={i} className="px-4 py-3 flex items-center justify-between hover:bg-bg-hover transition-colors">
                <div><div className="text-xs font-medium">{e.event}</div><div className="text-[10px] text-text-tertiary">{e.date}</div></div>
                <span className={`badge text-[10px] ${e.impact === 'high' ? 'badge-negative' : 'badge-warning'}`}>{e.impact}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
