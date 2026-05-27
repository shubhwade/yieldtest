'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, BarChart3 } from 'lucide-react';
import MetricCard from '@/components/cards/MetricCard';

const SECTORS = [
  { name: 'Government', avgYield: 4.35, spread: 0, change: -0.02, volume: '$45.2B', color: 'border-secondary/50' },
  { name: 'Corp IG', avgYield: 5.10, spread: 98, change: 0.03, volume: '$22.8B', color: 'border-positive/50' },
  { name: 'Corp HY', avgYield: 7.20, spread: 358, change: 0.12, volume: '$8.5B', color: 'border-accent/50' },
  { name: 'Municipal', avgYield: 3.45, spread: 45, change: -0.01, volume: '$6.2B', color: 'border-warning/50' },
  { name: 'MBS/ABS', avgYield: 5.60, spread: 135, change: -0.04, volume: '$15.3B', color: 'border-negative/50' },
  { name: 'TIPS', avgYield: 2.10, spread: -215, change: 0.01, volume: '$3.8B', color: 'border-text-tertiary/50' },
];

const ETFS = [
  { ticker: 'TLT', name: '20+ Year Treasury', price: 95.30, change: 0.45, ytd: -8.2, aum: '$38.5B' },
  { ticker: 'AGG', name: 'US Aggregate Bond', price: 87.50, change: -0.05, ytd: -3.1, aum: '$88.2B' },
  { ticker: 'BND', name: 'Total Bond Market', price: 72.10, change: -0.12, ytd: -2.8, aum: '$95.1B' },
  { ticker: 'LQD', name: 'IG Corporate', price: 108.20, change: -0.12, ytd: -1.5, aum: '$35.4B' },
  { ticker: 'HYG', name: 'High Yield', price: 77.80, change: 0.08, ytd: 2.1, aum: '$16.7B' },
  { ticker: 'MUB', name: 'National Muni', price: 107.50, change: 0.15, ytd: 1.2, aum: '$28.9B' },
  { ticker: 'SHY', name: '1-3 Year Treasury', price: 82.10, change: 0.02, ytd: 0.8, aum: '$24.3B' },
  { ticker: 'IEF', name: '7-10 Year Treasury', price: 93.40, change: 0.22, ytd: -4.5, aum: '$28.1B' },
  { ticker: 'TIP', name: 'TIPS Bond', price: 105.60, change: -0.08, ytd: -1.2, aum: '$19.8B' },
  { ticker: 'SGOV', name: '0-3 Month T-Bill', price: 100.05, change: 0.01, ytd: 2.6, aum: '$32.5B' },
];

export default function MarketsPage() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <h1 className="text-lg font-bold">Markets Overview</h1>

      {/* Sector Performance */}
      <div>
        <h2 className="section-title mb-3">Sector Performance</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          {SECTORS.map((s, i) => (
            <div key={i} className={`panel p-4 card-hover border-l-2 ${s.color}`}>
              <div className="text-xs text-text-secondary mb-1">{s.name}</div>
              <div className="font-mono text-xl font-bold">{s.avgYield.toFixed(2)}%</div>
              <div className="flex justify-between mt-2">
                <span className="text-[10px] text-text-tertiary">Spread: {s.spread}bps</span>
                <span className={`text-xs font-mono ${s.change > 0 ? 'text-positive' : 'text-negative'}`}>
                  {s.change > 0 ? '+' : ''}{s.change.toFixed(3)}
                </span>
              </div>
              <div className="text-[10px] text-text-tertiary mt-1">Vol: {s.volume}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Bond ETF Tracker */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold">Bond ETF Tracker</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-header">Ticker</th>
                <th className="table-header">Name</th>
                <th className="table-header text-right">Price</th>
                <th className="table-header text-right">Change</th>
                <th className="table-header text-right">YTD %</th>
                <th className="table-header text-right">AUM</th>
              </tr>
            </thead>
            <tbody>
              {ETFS.map((e, i) => (
                <tr key={i} className="table-row">
                  <td className="table-cell font-mono font-semibold text-accent">{e.ticker}</td>
                  <td className="table-cell text-xs">{e.name}</td>
                  <td className="table-cell text-right font-mono">${e.price.toFixed(2)}</td>
                  <td className={`table-cell text-right font-mono ${e.change > 0 ? 'text-positive' : 'text-negative'}`}>
                    {e.change > 0 ? '+' : ''}{e.change.toFixed(2)}
                  </td>
                  <td className={`table-cell text-right font-mono ${e.ytd > 0 ? 'text-positive' : 'text-negative'}`}>
                    {e.ytd > 0 ? '+' : ''}{e.ytd.toFixed(1)}%
                  </td>
                  <td className="table-cell text-right text-text-secondary text-xs">{e.aum}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
