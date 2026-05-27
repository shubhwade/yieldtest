'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Calculator } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function AnalyticsPage() {
  const [inputs, setInputs] = useState({ price: '98.50', coupon: '4.25', years: '10', frequency: '2', faceValue: '100' });
  const [results, setResults] = useState<any>(null);
  const [scenarioData, setScenarioData] = useState<{ yieldChange: number; price: number; pctChange: number }[]>([]);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  const calculate = async () => {
    const params = { price: parseFloat(inputs.price), coupon: parseFloat(inputs.coupon), years_to_maturity: parseFloat(inputs.years), frequency: parseInt(inputs.frequency), face_value: parseFloat(inputs.faceValue) };
    try {
      const res = await fetch(`${API_URL}/api/v1/analytics/calculate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) });
      if (res.ok) { const json = await res.json(); setResults(json.data); }
    } catch {
      // Fallback calc
      const ytm = (parseFloat(inputs.coupon) + (100 - parseFloat(inputs.price)) / parseFloat(inputs.years)) / ((100 + parseFloat(inputs.price)) / 2) * 100;
      setResults({ ytm: ytm.toFixed(4), current_yield: (parseFloat(inputs.coupon) / parseFloat(inputs.price) * 100).toFixed(4), macaulay_duration: (parseFloat(inputs.years) * 0.85).toFixed(4), modified_duration: (parseFloat(inputs.years) * 0.82).toFixed(4), dv01: 0.082, convexity: (parseFloat(inputs.years) * parseFloat(inputs.years) * 0.012).toFixed(4) });
    }
    // Generate scenario data
    const scenarios = [];
    for (let shift = -200; shift <= 200; shift += 25) {
      const baseYtm = parseFloat(inputs.coupon) / parseFloat(inputs.price) * 100;
      const newYtm = baseYtm + shift / 100;
      const dur = parseFloat(inputs.years) * 0.82;
      const pctChange = -dur * (shift / 100) + 0.5 * dur * dur * 0.01 * (shift / 100) ** 2;
      const newPrice = parseFloat(inputs.price) * (1 + pctChange / 100);
      scenarios.push({ yieldChange: shift, price: parseFloat(newPrice.toFixed(2)), pctChange: parseFloat(pctChange.toFixed(2)) });
    }
    setScenarioData(scenarios);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <h1 className="text-lg font-bold">Yield Analytics Engine</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Calculator Input */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2"><Calculator className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">Bond Calculator</span></div>
          </div>
          <div className="p-4 space-y-3">
            {[
              { label: 'Price ($)', key: 'price', step: '0.01' },
              { label: 'Coupon Rate (%)', key: 'coupon', step: '0.125' },
              { label: 'Years to Maturity', key: 'years', step: '0.5' },
              { label: 'Face Value ($)', key: 'faceValue', step: '1' },
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-text-secondary mb-1 block">{f.label}</label>
                <input className="input-field w-full" type="number" step={f.step} value={(inputs as any)[f.key]} onChange={e => setInputs({ ...inputs, [f.key]: e.target.value })} />
              </div>
            ))}
            <div>
              <label className="text-xs text-text-secondary mb-1 block">Frequency</label>
              <select className="input-field w-full" value={inputs.frequency} onChange={e => setInputs({ ...inputs, frequency: e.target.value })}>
                <option value="1">Annual</option><option value="2">Semi-Annual</option><option value="4">Quarterly</option>
              </select>
            </div>
            <button onClick={calculate} className="btn-primary w-full">Calculate Analytics</button>
          </div>
        </div>

        {/* Results */}
        <div className="panel lg:col-span-2">
          <div className="panel-header"><span className="text-sm font-semibold">Analytics Results</span></div>
          <div className="p-4">
            {results ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'YTM', value: `${(results.ytm * (results.ytm < 1 ? 100 : 1)).toFixed(3)}%`, color: 'text-accent' },
                  { label: 'Current Yield', value: `${(results.current_yield * (results.current_yield < 1 ? 100 : 1)).toFixed(3)}%`, color: 'text-blueAccent' },
                  { label: 'Mac. Duration', value: `${results.macaulay_duration}y`, color: 'text-text' },
                  { label: 'Mod. Duration', value: `${results.modified_duration}y`, color: 'text-text' },
                  { label: 'DV01', value: `$${results.dv01}`, color: 'text-secondary' },
                  { label: 'Convexity', value: results.convexity, color: 'text-text' },
                  { label: 'Theo. Price', value: results.theoretical_price ? `$${results.theoretical_price}` : '—', color: 'text-positive' },
                  { label: 'Accrued Int.', value: `$${results.accrued_interest || 0}`, color: 'text-text-secondary' },
                ].map((r, i) => (
                  <div key={i} className="bg-bg-panel rounded-lg p-3 border border-border">
                    <div className="text-[10px] text-text-secondary uppercase tracking-wider">{r.label}</div>
                    <div className={`font-mono text-lg font-bold mt-1 ${r.color}`}>{r.value}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-text-tertiary text-sm">Enter bond parameters and click Calculate</div>
            )}
          </div>
        </div>
      </div>

      {/* Scenario Analysis */}
      {scenarioData.length > 0 && (
        <div className="panel">
          <div className="panel-header"><span className="text-sm font-semibold">Scenario Analysis — Price Sensitivity</span></div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={scenarioData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="yieldChange" tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} tickFormatter={(v: number) => `${v > 0 ? '+' : ''}${v}bp`} />
                <YAxis tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} tickFormatter={(v: number) => `$${v}`} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#F8FAFC', fontSize: 12 }} />
                <Line type="monotone" dataKey="price" stroke="#2563EB" strokeWidth={2} dot={false} name="Price ($)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </motion.div>
  );
}
