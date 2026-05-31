import { useEffect, useState, useRef, useCallback } from 'react';
import { Search, User, Activity, Database, Cpu, AlertTriangle, ShieldCheck, Clock, RefreshCw } from 'lucide-react';

const tickerItems = [
  { label: '10Y', value: 4.25, change: -0.03 },
  { label: '2Y', value: 4.45, change: 0.05 },
  { label: '30Y', value: 4.52, change: -0.02 },
  { label: 'FFR', value: 5.33, change: 0 },
  { label: 'SOFR', value: 5.31, change: -0.01 },
  { label: 'CPI', value: 3.2, change: -0.1 },
  { label: 'IG Spd', value: 98, change: -2 },
  { label: 'HY Spd', value: 358, change: 5 },
  { label: 'TLT', value: 95.30, change: 0.45 },
  { label: 'LQD', value: 108.20, change: -0.12 },
  { label: 'HYG', value: 77.80, change: 0.08 },
  { label: 'AGG', value: 87.50, change: -0.05 },
];

export default function TopBar() {
  const [time, setTime] = useState('');
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [latencyLogs, setLatencyLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const telemetryRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    const update = () => setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch Telemetry Data
  const fetchTelemetry = useCallback(async () => {
    setLoading(true);
    try {
      const hRes = await fetch(`${API_URL}/api/v1/telemetry/health`);
      if (hRes.ok) {
        const json = await hRes.json();
        if (json.success) setTelemetry(json.data);
      }

      const aRes = await fetch(`${API_URL}/api/v1/telemetry/alerts`);
      if (aRes.ok) {
        const json = await aRes.json();
        if (json.success) setAlerts(json.data);
      }

      const lRes = await fetch(`${API_URL}/api/v1/telemetry/latency`);
      if (lRes.ok) {
        const json = await lRes.json();
        if (json.success) setLatencyLogs(json.data.slice(0, 5));
      }
    } catch (e) {
      console.error('Failed to load telemetry stats:', e);
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    if (showTelemetry) {
      fetchTelemetry();
      const interval = setInterval(fetchTelemetry, 8000);
      return () => clearInterval(interval);
    }
  }, [showTelemetry, fetchTelemetry]);

  // Click outside to close telemetry popover
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (telemetryRef.current && !telemetryRef.current.contains(e.target as Node)) {
        setShowTelemetry(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const resolveAlert = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/telemetry/resolve/${id}`, { method: 'POST' });
      if (res.ok) {
        fetchTelemetry();
      }
    } catch (e) {
      console.error('Error resolving telemetry alert:', e);
    }
  };

  const openSearch = () => {
    window.dispatchEvent(new CustomEvent('yl_open_search'));
  };

  return (
    <div className="h-10 bg-bg-panel border-b border-border flex items-center shrink-0 relative z-40">
      {/* Scrolling Ticker */}
      <div className="flex-1 overflow-hidden relative">
        <div className="flex animate-ticker whitespace-nowrap">
          {[...tickerItems, ...tickerItems].map((item, i) => (
            <div key={i} className="inline-flex items-center gap-1.5 px-4 text-xs">
              <span className="text-text-secondary font-medium">{item.label}</span>
              <span className="font-mono text-text font-semibold">{item.value.toFixed(2)}</span>
              <span className={`font-mono text-[11px] ${item.change > 0 ? 'text-positive' : item.change < 0 ? 'text-negative' : 'text-text-tertiary'}`}>
                {item.change > 0 ? '▲' : item.change < 0 ? '▼' : '—'}{Math.abs(item.change).toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3 px-4 border-l border-border shrink-0 relative" ref={telemetryRef}>
        {/* Observability Indicator */}
        <button
          onClick={() => setShowTelemetry(!showTelemetry)}
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono border transition-all ${
            alerts.length > 0
              ? 'bg-negative/10 border-negative/40 text-negative hover:bg-negative/20 animate-pulse'
              : 'bg-positive/10 border-positive/30 text-positive hover:bg-positive/20'
          }`}
        >
          <Activity className="w-3.5 h-3.5 shrink-0" />
          <span>{alerts.length > 0 ? 'DISCREPANCY' : '98% CONFIDENCE'}</span>
        </button>

        {/* Telemetry Popover Dropdown */}
        {showTelemetry && (
          <div className="absolute right-4 top-9 w-96 bg-[#0E0E0E] border border-border rounded-lg shadow-2xl p-4 space-y-4 z-50 text-xs text-text-secondary">
            <div className="flex items-center justify-between border-b border-border/80 pb-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-positive" />
                <span className="font-bold text-text uppercase tracking-wider font-mono">Telemetry Observability</span>
              </div>
              <button onClick={fetchTelemetry} disabled={loading} className="text-text-tertiary hover:text-text">
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {telemetry ? (
              <div className="space-y-4">
                {/* Latency & Quality Row */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-bg-panel/40 border border-border/60 rounded p-2 text-center">
                    <div className="text-[10px] text-text-tertiary uppercase">DB Latency</div>
                    <div className="font-mono text-sm font-bold text-text flex items-center justify-center gap-1 mt-0.5">
                      <Database className="w-3.5 h-3.5 text-accent" />
                      {telemetry.database?.latency_ms} ms
                    </div>
                  </div>
                  <div className="bg-bg-panel/40 border border-border/60 rounded p-2 text-center">
                    <div className="text-[10px] text-text-tertiary uppercase">Host CPU / Memory</div>
                    <div className="font-mono text-sm font-bold text-text flex items-center justify-center gap-1 mt-0.5">
                      <Cpu className="w-3.5 h-3.5 text-secondary" />
                      {telemetry.infrastructure?.cpu_usage_pct}%
                    </div>
                  </div>
                </div>

                {/* Freshness list */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider">Telemetry Freshness Engine</div>
                  <div className="flex items-center justify-between font-mono bg-bg-panel/30 p-1.5 rounded">
                    <span>Treasury Yield Curve</span>
                    <span className="text-positive font-bold">{telemetry.data_quality?.treasury_yield_curve?.freshness_status} ({telemetry.data_quality?.treasury_yield_curve?.age_seconds}s)</span>
                  </div>
                </div>

                {/* Multi-Source Validation Alerts */}
                <div className="space-y-2">
                  <div className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-accent" />
                    <span>Discrepancy Alerts ({alerts.length})</span>
                  </div>
                  <div className="space-y-1.5 max-h-24 overflow-y-auto pr-1">
                    {alerts.length === 0 ? (
                      <div className="text-[10px] text-text-tertiary italic text-center p-2 bg-bg-panel/20 rounded">
                        100% consensus across FRED, TreasuryDirect & SEC.
                      </div>
                    ) : (
                      alerts.map((alert) => (
                        <div key={alert._id} className="bg-negative/5 border border-negative/30 rounded p-2 flex flex-col gap-1">
                          <div className="text-[10px] font-bold text-negative uppercase">
                            {alert.severity} • {alert.category}
                          </div>
                          <div className="text-[10px] text-text leading-tight">{alert.message}</div>
                          <button
                            onClick={() => resolveAlert(alert._id)}
                            className="self-end text-[9px] bg-negative/20 text-negative hover:bg-negative/30 px-1.5 py-0.5 rounded font-mono mt-1"
                          >
                            ACKNOWLEDGE & RESOLVE
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Rolling latency logs */}
                <div className="space-y-2">
                  <div className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-text-tertiary" />
                    <span>External API Latency Logs</span>
                  </div>
                  <div className="font-mono text-[10px] space-y-1 bg-bg-panel/40 p-2 rounded max-h-24 overflow-y-auto">
                    {latencyLogs.map((log, idx) => (
                      <div key={idx} className="flex justify-between border-b border-border/20 pb-0.5 last:border-0">
                        <span className="text-text-secondary">{log.source} {log.endpoint}</span>
                        <span className="text-accent">{log.latency_ms?.toFixed(1)} ms</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-text-tertiary">Loading diagnostic metrics...</div>
            )}
          </div>
        )}

        <div className="flex items-center gap-1.5 text-xs text-text-tertiary">
          <span className="font-mono">{time}</span>
        </div>

        <button onClick={openSearch} className="p-1 text-text-secondary hover:text-text transition-colors">
          <Search className="w-4 h-4" />
        </button>

        <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center">
          <User className="w-4 h-4 text-accent" />
        </div>
      </div>
    </div>
  );
}

