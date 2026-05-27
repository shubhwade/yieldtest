'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import MetricCard from '@/components/MetricCard';

const YieldCurveChart = dynamic(() => import('@/charts/YieldCurveChart'), { ssr: false });
const SpreadChart = dynamic(() => import('@/charts/SpreadChart'), { ssr: false });

import { TrendingUp, TrendingDown, Activity, BarChart3, Brain, Eye, Bell, Zap, Clock } from 'lucide-react';
import { io } from 'socket.io-client';
import { MOCK_METRICS, MOCK_CURVE, MOCK_SPREADS, MOCK_RATES } from '@/utils/mocks';

const MOCK_HEATMAP = [
  { name: 'Government', yield: 4.35, change: -0.02, color: 'bg-secondary' },
  { name: 'Corp IG', yield: 5.10, change: 0.03, color: 'bg-accent' },
  { name: 'Corp HY', yield: 7.20, change: 0.12, color: 'bg-dark' },
  { name: 'Municipal', yield: 3.45, change: -0.01, color: 'bg-blueAccent' },
  { name: 'MBS', yield: 5.60, change: -0.04, color: 'bg-secondary' },
  { name: 'TIPS', yield: 2.10, change: 0.01, color: 'bg-light' },
];

const MOCK_MOVERS = [
  { name: 'Tesla Inc. 5.125% 08/2030', type: 'corporate', change: 0.18 },
  { name: 'U.S. Treasury 10Y 4.250%', type: 'treasury', change: -0.12 },
  { name: 'Apple Inc. 3.750% 05/2033', type: 'corporate', change: 0.08 },
  { name: 'State of California GO 4.0%', type: 'municipal', change: -0.06 },
  { name: 'Ford Motor 6.500% 2028', type: 'corporate', change: 0.15 },
];

const MOCK_BRIEF = `**Treasury Market**: The yield curve remains inverted with 10Y at 4.25% and 2Y at 4.45%. Inversion depth narrowed slightly, suggesting markets are adjusting rate cut expectations.

**Credit Markets**: IG spreads tightened 2bps to 98bps, while HY spreads widened 5bps to 358bps, signaling cautious risk appetite.

**Outlook**: Watch for Friday's employment data which could shift Fed pivot timing. Municipal bonds continue offering attractive tax-equivalent yields for high-bracket investors.`;

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(MOCK_METRICS);
  const [curve, setCurve] = useState(MOCK_CURVE);
  const [spreads, setSpreads] = useState(MOCK_SPREADS);
  const [rates, setRates] = useState(MOCK_RATES);
  const [heatmap, setHeatmap] = useState(MOCK_HEATMAP);
  const [movers, setMovers] = useState(MOCK_MOVERS);
  const [brief, setBrief] = useState(MOCK_BRIEF);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const res = await fetch(`${API_URL}/api/v1/market/dashboard`);
        if (res.ok) {
          const json = await res.json();
          const d = json.data;
          if (d?.key_metrics?.length) {
            setMetrics(d.key_metrics.map((m: any) => ({
              label: m.label, value: m.value?.toFixed(3) ?? '—', change: m.change, unit: m.unit,
            })));
          }
          if (d?.yield_curve?.curve) {
            const c = d.yield_curve.curve;
            const curveData = Object.entries(c).map(([mat, val]: any) => ({
              maturity: mat, yield: val.value ?? 0,
            }));
            if (curveData.some((p: any) => p.yield > 0)) setCurve(curveData);
          }
          if (d?.spreads?.length) setSpreads(d.spreads);
          if (d?.rate_movements?.length) setRates(d.rate_movements.map((r: any) => ({
            name: r.name, current: r.current, d1: r.change_1d, w1: r.change_1w, m1: r.change_1m,
          })));
          if (d?.heatmap?.sectors) setHeatmap(d.heatmap.sectors.map((s: any) => ({
            name: s.name, yield: s.avg_yield, change: s.change
          })));
          if (d?.movers?.length) setMovers(d.movers);
        }

        // Fetch Watchlist
        const wRes = await fetch(`${API_URL}/api/v1/watchlist/`);
        if (wRes.ok) {
          const wJson = await wRes.json();
          if (wJson.success) setWatchlist(wJson.data.slice(0, 3));
        }

        // Fetch Alerts
        const aRes = await fetch(`${API_URL}/api/v1/alerts/triggered`);
        if (aRes.ok) {
          const aJson = await aRes.json();
          if (aJson.success) setAlerts(aJson.data.slice(0, 3));
        }

      } catch (e) {
        console.error("Dashboard fetch error:", e);
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000); // Poll every 60s as backup

    // Real-time Socket Integration
    const socket = io(API_URL);
    
    socket.on('market_update', (data) => {
      console.log('Real-time market update:', data);
      if (data.metrics) {
        setMetrics(data.metrics.map((m: any) => ({
          label: m.label, value: m.value?.toFixed(3) ?? '—', change: m.change, unit: m.unit,
        })));
      }
      if (data.curve?.curve) {
        const curveData = Object.entries(data.curve.curve).map(([mat, val]: any) => ({
          maturity: mat, yield: val.value ?? 0,
        }));
        setCurve(curveData);
      }
    });

    socket.on('dashboard_refresh', (data) => {
      console.log('Real-time dashboard refresh:', data);
      if (data.key_metrics) {
        setMetrics(data.key_metrics.map((m: any) => ({
          label: m.label, value: m.value?.toFixed(3) ?? '—', change: m.change, unit: m.unit,
        })));
      }
      if (data.yield_curve?.curve) {
        const curveData = Object.entries(data.yield_curve.curve).map(([mat, val]: any) => ({
          maturity: mat, yield: val.value ?? 0,
        }));
        setCurve(curveData);
      }
      if (data.rate_movements) {
        setRates(data.rate_movements.map((r: any) => ({
          name: r.name, current: r.current, d1: r.change_1d, w1: r.change_1w, m1: r.change_1m,
        })));
      }
    });

    socket.on('ai_brief_update', (data) => {
      if (data.brief) setBrief(data.brief);
    });

    return () => {
      clearInterval(interval);
      socket.disconnect();
    };
  }, [API_URL]);

  const changeColor = (v: number) => v > 0 ? 'text-positive' : v < 0 ? 'text-negative' : 'text-text-tertiary';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-text">Market Dashboard</h1>
          <p className="text-xs text-text-tertiary">Real-time fixed income market overview</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-text-tertiary">
          <div className="w-1.5 h-1.5 rounded-full bg-positive animate-pulse" />
          LIVE
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {metrics.map((m, i) => (
          <MetricCard key={i} label={m.label} value={m.value} change={m.change} unit={m.unit} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Yield Curve */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold">Treasury Yield Curve</span>
            </div>
            <span className="text-xs text-text-tertiary">11 maturities</span>
          </div>
          <div className="p-4">
            <YieldCurveChart data={curve} height={280} />
          </div>
        </div>

        {/* Spread Monitor */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-secondary" />
              <span className="text-sm font-semibold">Spread Monitor</span>
            </div>
            <span className="text-xs text-text-tertiary">Credit & Curve</span>
          </div>
          <div className="p-4">
            <SpreadChart data={spreads} height={280} />
          </div>
        </div>
      </div>

      {/* Third Row — Rates, Heatmap, AI Brief */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Rate Movements */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold">Rate Movements</span>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="table-header">Rate</th>
                  <th className="table-header text-right">Current</th>
                  <th className="table-header text-right">1D</th>
                  <th className="table-header text-right">1W</th>
                  <th className="table-header text-right">1M</th>
                </tr>
              </thead>
              <tbody>
                {rates.map((r, i) => (
                  <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                    <td className="table-cell text-text text-xs font-medium">{r.name}</td>
                    <td className="table-cell text-right font-mono text-xs">{r.current?.toFixed(2)}</td>
                    <td className={`table-cell text-right font-mono text-xs ${changeColor(r.d1)}`}>{r.d1 > 0 ? '+' : ''}{r.d1?.toFixed(3)}</td>
                    <td className={`table-cell text-right font-mono text-xs ${changeColor(r.w1)}`}>{r.w1 > 0 ? '+' : ''}{r.w1?.toFixed(3)}</td>
                    <td className={`table-cell text-right font-mono text-xs ${changeColor(r.m1)}`}>{r.m1 > 0 ? '+' : ''}{r.m1?.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Market Heatmap */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-secondary" />
              <span className="text-sm font-semibold">Market Heatmap</span>
            </div>
          </div>
          <div className="panel-body">
            <div className="grid grid-cols-2 gap-2">
              {heatmap.map((sector, i) => (
                <div
                  key={i}
                  className={`rounded-lg p-3 border border-border bg-bg-card transition-all hover:scale-[1.02] hover:border-accent/30`}
                >
                  <div className="text-xs text-text-secondary mb-1">{sector.name}</div>
                  <div className="font-mono text-sm font-bold">{sector.yield?.toFixed(2)}%</div>
                  <div className={`text-xs font-mono ${sector.change > 0 ? 'text-positive' : sector.change < 0 ? 'text-negative' : 'text-text-tertiary'}`}>
                    {sector.change > 0 ? '+' : ''}{sector.change?.toFixed(3)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* AI Daily Brief */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold">AI Daily Brief</span>
            </div>
            <span className="badge-accent">Gemini</span>
          </div>
          <div className="panel-body">
            <div className="text-xs text-text-secondary leading-relaxed whitespace-pre-line font-mono">
              {brief}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row — Movers, Watchlist, Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Top Movers */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-negative" />
              <span className="text-sm font-semibold">Top Movers</span>
            </div>
          </div>
          <div className="divide-y divide-border/50">
            {movers.map((m, i) => (
              <div key={i} className={`px-4 py-2.5 flex items-center justify-between hover:bg-bg-hover transition-colors cursor-pointer ${i % 2 === 1 ? 'bg-bg-panel/50' : ''}`}>
                <div>
                  <div className="text-xs text-text font-medium truncate max-w-[200px]">{m.name}</div>
                  <div className="text-[10px] text-text-tertiary uppercase">{m.type}</div>
                </div>
                <span className={`font-mono text-xs font-semibold ${m.change > 0 ? 'text-positive' : 'text-negative'}`}>
                  {m.change > 0 ? '+' : ''}{m.change?.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Watchlist */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-secondary" />
              <span className="text-sm font-semibold">Watchlist</span>
            </div>
            <span className="text-xs text-text-tertiary">{watchlist.length} bonds</span>
          </div>
          <div className="divide-y divide-border/50">
            {watchlist.length === 0 ? (
              <div className="p-4 text-center text-[10px] text-text-tertiary">No bonds in watchlist.</div>
            ) : watchlist.map((b, i) => (
              <div key={i} className={`px-4 py-2.5 flex items-center justify-between hover:bg-bg-hover transition-colors cursor-pointer ${i % 2 === 1 ? 'bg-bg-panel/50' : ''}`}>
                <div className="text-xs text-text font-medium truncate max-w-[180px]">{b.name || b.issuer}</div>
                <div className="text-right">
                  <div className="font-mono text-xs">{b.price?.toFixed(2)}</div>
                  <div className="font-mono text-[10px] text-accent">{b.ytm?.toFixed(2)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold">Recent Alerts</span>
            </div>
          </div>
          <div className="divide-y divide-border/50">
            {alerts.length === 0 ? (
              <div className="p-4 text-center text-[10px] text-text-tertiary">No recently triggered alerts.</div>
            ) : alerts.map((a, i) => (
              <div key={i} className={`px-4 py-2.5 flex items-center gap-3 hover:bg-bg-hover transition-colors cursor-pointer ${i % 2 === 1 ? 'bg-bg-panel/50' : ''}`}>
                <div className={`w-2 h-2 rounded-full shrink-0 ${a.type === 'yield_change' ? 'bg-accent' : 'bg-negative'}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-text truncate">{a.target} {a.condition} {a.threshold}%</div>
                  <div className="text-[10px] text-text-tertiary">{new Date(a.triggered_at).toLocaleTimeString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
