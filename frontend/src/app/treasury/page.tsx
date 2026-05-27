'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, CheckCircle } from 'lucide-react';
import YieldCurveChart from '@/components/charts/YieldCurveChart';

const MOCK_CURVE = [
  { maturity: '1M', yield: 5.35 }, { maturity: '3M', yield: 5.30 }, { maturity: '6M', yield: 5.22 },
  { maturity: '1Y', yield: 5.00 }, { maturity: '2Y', yield: 4.45 }, { maturity: '3Y', yield: 4.30 },
  { maturity: '5Y', yield: 4.18 }, { maturity: '7Y', yield: 4.22 }, { maturity: '10Y', yield: 4.25 },
  { maturity: '20Y', yield: 4.48 }, { maturity: '30Y', yield: 4.52 },
];

const MOCK_AUCTIONS = [
  { desc: '4-Week Bill', type: 'Bill', date: '2026-06-02', rate: '5.28%' },
  { desc: '13-Week Bill', type: 'Bill', date: '2026-06-03', rate: '5.22%' },
  { desc: '2-Year Note', type: 'Note', date: '2026-06-05', rate: '4.45%' },
  { desc: '5-Year Note', type: 'Note', date: '2026-06-08', rate: '4.18%' },
  { desc: '10-Year Note', type: 'Note', date: '2026-06-10', rate: '4.25%' },
  { desc: '30-Year Bond', type: 'Bond', date: '2026-06-15', rate: '4.52%' },
];

export default function TreasuryPage() {
  const [curve, setCurve] = useState(MOCK_CURVE);
  const [inversions, setInversions] = useState({ '10Y_2Y': { spread: -0.20, inverted: true }, '10Y_3M': { spread: -1.05, inverted: true } });
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    async function fetchData() {
      try {
        const [curveRes, invRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/fred/yield-curve`),
          fetch(`${API_URL}/api/v1/fred/inversion`),
        ]);
        if (curveRes.ok) {
          const j = await curveRes.json();
          if (j.data?.curve) {
            setCurve(Object.entries(j.data.curve).map(([m, v]: any) => ({ maturity: m, yield: v.value ?? 0 })));
          }
        }
        if (invRes.ok) {
          const j = await invRes.json();
          if (j.data?.inversions) setInversions(j.data.inversions);
        }
      } catch { /* mock */ }
    }
    fetchData();
  }, [API_URL]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <h1 className="text-lg font-bold">Treasury Yield Curve</h1>

      {/* Main Curve Chart */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2"><Activity className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">Live Yield Curve</span></div>
          <span className="text-xs text-text-tertiary">11 maturities • 1M to 30Y</span>
        </div>
        <div className="p-4">
          <YieldCurveChart data={curve} height={400} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Inversion Detection */}
        <div className="panel">
          <div className="panel-header"><span className="text-sm font-semibold">Inversion Analysis</span></div>
          <div className="p-4 space-y-4">
            {Object.entries(inversions).map(([key, data]: any) => (
              <div key={key} className={`rounded-lg p-4 border ${data.inverted ? 'border-negative/30 bg-negative/5' : 'border-positive/30 bg-positive/5'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {data.inverted ? <AlertTriangle className="w-5 h-5 text-negative" /> : <CheckCircle className="w-5 h-5 text-positive" />}
                    <span className="text-sm font-semibold">{key.replace('_', ' vs ')}</span>
                  </div>
                  <span className={`badge ${data.inverted ? 'badge-negative' : 'badge-positive'}`}>{data.inverted ? 'INVERTED' : 'NORMAL'}</span>
                </div>
                <div className="mt-2 font-mono text-2xl font-bold">{data.spread > 0 ? '+' : ''}{data.spread?.toFixed(2) ?? '—'}%</div>
                {data.inverted && <p className="text-xs text-text-secondary mt-1">⚠️ Historically a recession predictor with 12-24 month lead time</p>}
              </div>
            ))}
          </div>
        </div>

        {/* Auction Calendar */}
        <div className="panel">
          <div className="panel-header"><span className="text-sm font-semibold">Upcoming Auctions</span></div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr>
                <th className="table-header">Security</th><th className="table-header">Type</th><th className="table-header">Date</th><th className="table-header text-right">Est. Rate</th>
              </tr></thead>
              <tbody>
                {MOCK_AUCTIONS.map((a, i) => (
                  <tr key={i} className="table-row">
                    <td className="table-cell text-xs font-medium">{a.desc}</td>
                    <td className="table-cell"><span className="badge-secondary text-[10px]">{a.type}</span></td>
                    <td className="table-cell text-xs text-text-secondary">{a.date}</td>
                    <td className="table-cell text-right font-mono text-accent">{a.rate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
