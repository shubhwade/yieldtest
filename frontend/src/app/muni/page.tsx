'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Building2, Calculator } from 'lucide-react';

const MUNIS = [
  { name: 'California GO 4.0% 2035', state: 'CA', rating: 'AA-', coupon: 4.0, ytm: 3.45, price: 104.10, taxEquiv: 5.07 },
  { name: 'New York GO 3.5% 2033', state: 'NY', rating: 'AA', coupon: 3.5, ytm: 3.12, price: 105.80, taxEquiv: 4.59 },
  { name: 'Texas GO 3.75% 2040', state: 'TX', rating: 'AAA', coupon: 3.75, ytm: 3.55, price: 102.20, taxEquiv: 5.22 },
  { name: 'Illinois GO 5.0% 2030', state: 'IL', rating: 'BBB', coupon: 5.0, ytm: 4.85, price: 101.50, taxEquiv: 7.13 },
  { name: 'MTA NY Revenue 4.25% 2038', state: 'NY', rating: 'A', coupon: 4.25, ytm: 3.95, price: 103.40, taxEquiv: 5.81 },
  { name: 'LA DWP Revenue 3.25% 2032', state: 'CA', rating: 'AA', coupon: 3.25, ytm: 2.95, price: 106.10, taxEquiv: 4.34 },
  { name: 'Florida GO 3.0% 2036', state: 'FL', rating: 'AAA', coupon: 3.0, ytm: 2.80, price: 107.50, taxEquiv: 4.12 },
  { name: 'New Jersey GO 4.5% 2034', state: 'NJ', rating: 'A-', coupon: 4.5, ytm: 4.20, price: 103.00, taxEquiv: 6.18 },
];

const STATES = [
  { state: 'California', avgYield: 3.25, bonds: 45, rating: 'AA-' },
  { state: 'New York', avgYield: 3.10, bonds: 38, rating: 'AA' },
  { state: 'Texas', avgYield: 3.55, bonds: 30, rating: 'AAA' },
  { state: 'Florida', avgYield: 2.80, bonds: 25, rating: 'AAA' },
  { state: 'Illinois', avgYield: 4.85, bonds: 20, rating: 'BBB' },
  { state: 'Pennsylvania', avgYield: 3.45, bonds: 18, rating: 'AA-' },
  { state: 'New Jersey', avgYield: 4.20, bonds: 15, rating: 'A-' },
  { state: 'Ohio', avgYield: 3.35, bonds: 15, rating: 'AA' },
];

export default function MuniPage() {
  const [taxBracket, setTaxBracket] = useState(32);
  const [muniYield, setMuniYield] = useState(3.45);
  const taxEquiv = muniYield / (1 - taxBracket / 100);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <h1 className="text-lg font-bold">Municipal Bond Intelligence</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Tax Equiv Calculator */}
        <div className="panel">
          <div className="panel-header"><div className="flex items-center gap-2"><Calculator className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">Tax-Equivalent Yield</span></div></div>
          <div className="p-4 space-y-3">
            <div><label className="text-xs text-text-secondary mb-1 block">Muni Yield (%)</label><input className="input-field w-full" type="number" step="0.05" value={muniYield} onChange={e => setMuniYield(parseFloat(e.target.value) || 0)} /></div>
            <div><label className="text-xs text-text-secondary mb-1 block">Federal Tax Bracket (%)</label>
              <select className="input-field w-full" value={taxBracket} onChange={e => setTaxBracket(parseInt(e.target.value))}>
                {[10, 12, 22, 24, 32, 35, 37].map(r => <option key={r} value={r}>{r}%</option>)}
              </select>
            </div>
            <div className="bg-accent/10 rounded-lg p-4 border border-accent/20 text-center">
              <div className="text-xs text-accent mb-1">Tax-Equivalent Yield</div>
              <div className="font-mono text-3xl font-bold text-accent">{taxEquiv.toFixed(2)}%</div>
              <div className="text-xs text-text-secondary mt-1">vs. {muniYield}% tax-free muni yield</div>
            </div>
          </div>
        </div>

        {/* State Comparison */}
        <div className="panel lg:col-span-2">
          <div className="panel-header"><span className="text-sm font-semibold">State Comparison</span></div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr><th className="table-header">State</th><th className="table-header text-right">Avg Yield</th><th className="table-header text-right">Bonds</th><th className="table-header">Rating</th><th className="table-header text-right">Tax Equiv (32%)</th></tr></thead>
              <tbody>{STATES.map((s, i) => (
                <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                  <td className="table-cell text-xs font-medium">{s.state}</td>
                  <td className="table-cell text-right font-mono text-accent">{s.avgYield.toFixed(2)}%</td>
                  <td className="table-cell text-right font-mono">{s.bonds}</td>
                  <td className="table-cell"><span className={`font-mono font-semibold ${s.rating.startsWith('AAA') ? 'text-positive' : s.rating.startsWith('AA') ? 'text-positive' : s.rating.startsWith('A') ? 'text-blueAccent' : 'text-warning'}`}>{s.rating}</span></td>
                  <td className="table-cell text-right font-mono text-positive">{(s.avgYield / 0.68).toFixed(2)}%</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Top Muni Bonds */}
      <div className="panel">
        <div className="panel-header"><div className="flex items-center gap-2"><Building2 className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">Top Municipal Bonds</span></div></div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr><th className="table-header">Name</th><th className="table-header">State</th><th className="table-header">Rating</th><th className="table-header text-right">Coupon</th><th className="table-header text-right">Price</th><th className="table-header text-right">YTM</th><th className="table-header text-right">Tax Equiv</th></tr></thead>
            <tbody>{MUNIS.map((m, i) => (
              <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                <td className="table-cell text-xs font-medium max-w-[200px] truncate">{m.name}</td>
                <td className="table-cell"><span className="badge-secondary text-[10px]">{m.state}</span></td>
                <td className="table-cell font-mono font-semibold text-positive">{m.rating}</td>
                <td className="table-cell text-right font-mono">{m.coupon.toFixed(2)}%</td>
                <td className="table-cell text-right font-mono">{m.price.toFixed(2)}</td>
                <td className="table-cell text-right font-mono text-accent">{m.ytm.toFixed(2)}%</td>
                <td className="table-cell text-right font-mono text-positive font-bold">{m.taxEquiv.toFixed(2)}%</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
