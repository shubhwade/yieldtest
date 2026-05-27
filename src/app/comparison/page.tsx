'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GitCompare, BarChart3 } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const INSTRUMENTS = {
  treasury: { name: 'Treasury', yield: 4.25, risk: 5, duration: 7.5, liquidity: 98, taxImpact: 85, creditQuality: 100, inflationProtection: 20, volatility: 15, sharpe: 0.85, defaultProb: 0 },
  corporate_ig: { name: 'Corp IG', yield: 5.10, risk: 25, duration: 6.2, liquidity: 85, taxImpact: 70, creditQuality: 80, inflationProtection: 15, volatility: 25, sharpe: 0.72, defaultProb: 0.5 },
  corporate_hy: { name: 'Corp HY', yield: 7.20, risk: 65, duration: 4.1, liquidity: 60, taxImpact: 70, creditQuality: 35, inflationProtection: 10, volatility: 55, sharpe: 0.45, defaultProb: 4.2 },
  municipal: { name: 'Municipal', yield: 3.45, risk: 20, duration: 8.5, liquidity: 55, taxImpact: 100, creditQuality: 85, inflationProtection: 10, volatility: 18, sharpe: 0.90, defaultProb: 0.1 },
  tips: { name: 'TIPS', yield: 2.10, risk: 10, duration: 6.8, liquidity: 90, taxImpact: 75, creditQuality: 100, inflationProtection: 95, volatility: 12, sharpe: 0.65, defaultProb: 0 },
  bond_etf: { name: 'Bond ETF', yield: 4.65, risk: 20, duration: 5.5, liquidity: 99, taxImpact: 72, creditQuality: 75, inflationProtection: 15, volatility: 20, sharpe: 0.70, defaultProb: 0.2 },
  cd: { name: 'CD', yield: 5.00, risk: 2, duration: 2.0, liquidity: 30, taxImpact: 65, creditQuality: 100, inflationProtection: 5, volatility: 0, sharpe: 1.2, defaultProb: 0 },
  money_market: { name: 'Money Market', yield: 5.20, risk: 1, duration: 0.1, liquidity: 100, taxImpact: 65, creditQuality: 100, inflationProtection: 5, volatility: 0.5, sharpe: 1.5, defaultProb: 0 },
};

type InstrumentKey = keyof typeof INSTRUMENTS;

export default function ComparisonPage() {
  const [selected, setSelected] = useState<InstrumentKey[]>(['treasury', 'corporate_ig', 'municipal', 'tips']);

  const selectedData = selected.map(k => INSTRUMENTS[k]);
  const radarData = ['Yield', 'Safety', 'Liquidity', 'Tax Eff.', 'Credit', 'Infl. Prot.'].map((metric, i) => {
    const row: any = { metric };
    selectedData.forEach(d => {
      row[d.name] = [d.yield * 10, 100 - d.risk, d.liquidity, d.taxImpact, d.creditQuality, d.inflationProtection][i];
    });
    return row;
  });

  const colors = ['#2563EB', '#3B82F6', '#1E40AF', '#60A5FA', '#38BDF8', '#22C55E'];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-text">Fixed Income Comparison</h1>
          <p className="text-xs text-text-tertiary">Side-by-side instrument analysis</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end max-w-md">
          {(Object.keys(INSTRUMENTS) as InstrumentKey[]).map(k => (
            <button key={k} onClick={() => setSelected(prev => prev.includes(k) ? prev.filter(x => x !== k) : [...prev, k].slice(0, 4))}
              className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border transition-all duration-200 ${selected.includes(k) ? 'border-accent bg-accent/10 text-accent font-bold' : 'border-border text-text-secondary hover:border-accent/30 hover:bg-bg-hover'}`}>
              {INSTRUMENTS[k].name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar Chart */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold">Risk-Return Profile</span>
            </div>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#CBD5E1', fontSize: 11 }} />
                {selectedData.map((d, i) => (
                  <Radar key={d.name} name={d.name} dataKey={d.name} stroke={colors[i]} fill={colors[i]} fillOpacity={0.15} strokeWidth={2} />
                ))}
                <Legend wrapperStyle={{ fontSize: 11, color: '#CBD5E1', paddingTop: '20px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Yield Comparison Bar */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blueAccent" />
              <span className="text-sm font-semibold">Yield Comparison</span>
            </div>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={selectedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} />
                <YAxis tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} tickFormatter={(v: number) => `${v}%`} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#F8FAFC', fontSize: 12 }} />
                <Bar dataKey="yield" fill="#2563EB" radius={[4, 4, 0, 0]} name="Yield %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="panel">
        <div className="panel-header"><span className="text-sm font-semibold">Detailed Comparison</span></div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-header">Metric</th>
                {selectedData.map(d => <th key={d.name} className="table-header text-center">{d.name}</th>)}
              </tr>
            </thead>
            <tbody>
              {[
                { label: 'Expected Yield', key: 'yield', fmt: (v: number) => `${v.toFixed(2)}%`, best: 'max' },
                { label: 'Risk Score', key: 'risk', fmt: (v: number) => `${v}/100`, best: 'min' },
                { label: 'Duration', key: 'duration', fmt: (v: number) => `${v.toFixed(1)}y`, best: 'min' },
                { label: 'Liquidity', key: 'liquidity', fmt: (v: number) => `${v}/100`, best: 'max' },
                { label: 'Tax Efficiency', key: 'taxImpact', fmt: (v: number) => `${v}/100`, best: 'max' },
                { label: 'Credit Quality', key: 'creditQuality', fmt: (v: number) => `${v}/100`, best: 'max' },
                { label: 'Inflation Prot.', key: 'inflationProtection', fmt: (v: number) => `${v}/100`, best: 'max' },
                { label: 'Volatility', key: 'volatility', fmt: (v: number) => `${v}%`, best: 'min' },
                { label: 'Sharpe Ratio', key: 'sharpe', fmt: (v: number) => v.toFixed(2), best: 'max' },
                { label: 'Default Prob.', key: 'defaultProb', fmt: (v: number) => `${v}%`, best: 'min' },
              ].map((row, i) => {
                const values = selectedData.map(d => (d as any)[row.key] as number);
                const bestVal = row.best === 'max' ? Math.max(...values) : Math.min(...values);
                return (
                  <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                    <td className="table-cell text-xs font-medium text-text-secondary">{row.label}</td>
                    {selectedData.map((d, j) => {
                      const val = (d as any)[row.key] as number;
                      const isBest = val === bestVal;
                      return (
                        <td key={j} className={`table-cell text-center font-mono text-sm ${isBest ? 'text-positive font-bold' : ''}`}>
                          {row.fmt(val)}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
