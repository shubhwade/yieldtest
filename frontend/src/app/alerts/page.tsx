'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Plus, Trash2, TrendingUp, Activity, Shield, Globe, BarChart3, X, AlertTriangle } from 'lucide-react';

const ALERT_TYPES = [
  { value: 'yield_change', label: 'Yield Change', icon: <TrendingUp className="w-3.5 h-3.5" /> },
  { value: 'spread', label: 'Spread Alert', icon: <BarChart3 className="w-3.5 h-3.5" /> },
  { value: 'inversion', label: 'Curve Inversion', icon: <Activity className="w-3.5 h-3.5" /> },
  { value: 'rating', label: 'Rating Change', icon: <Shield className="w-3.5 h-3.5" /> },
  { value: 'macro', label: 'Macro Event', icon: <Globe className="w-3.5 h-3.5" /> },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [triggered, setTriggered] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newAlert, setNewAlert] = useState({ type: 'yield_change', target: '', condition: 'above', threshold: '' });
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/alerts/`);
      const json = await res.json();
      if (json.success) setAlerts(json.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [API_URL]);

  const fetchTriggered = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/alerts/triggered`);
      const json = await res.json();
      if (json.success) setTriggered(json.data);
    } catch (e) { console.error(e); }
  }, [API_URL]);

  useEffect(() => {
    fetchAlerts();
    fetchTriggered();
  }, [fetchAlerts, fetchTriggered]);

  

  const handleCreate = async () => {
    if (!newAlert.target || !newAlert.threshold) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/alerts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAlert)
      });
      if ((await res.json()).success) {
        setShowForm(false);
        setNewAlert({ type: 'yield_change', target: '', condition: 'above', threshold: '' });
        fetchAlerts();
      }
    } catch (e) { alert("Error creating alert"); }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/alerts/${id}`, { method: 'DELETE' });
      if ((await res.json()).success) fetchAlerts();
    } catch (e) { alert("Error deleting alert"); }
  };

  if (loading) return <div className="p-8 text-center font-mono text-xs text-text-tertiary animate-pulse">Loading Alert Engine...</div>;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">Alerts & Monitoring</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-1"><Plus className="w-4 h-4" />New Alert</button>
      </div>

      <AnimatePresence>
        {showForm && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="panel bg-black border-accent/30 overflow-hidden">
            <div className="panel-header">
              <span className="text-sm font-semibold">Configure Real-Time Alert</span>
              <button onClick={() => setShowForm(false)}><X className="w-4 h-4 text-text-tertiary" /></button>
            </div>
            <div className="p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
              <div><label className="text-xs text-text-secondary mb-1 block uppercase">Metric Type</label><select className="input-field w-full" value={newAlert.type} onChange={e => setNewAlert({...newAlert, type: e.target.value})}>{ALERT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}</select></div>
              <div><label className="text-xs text-text-secondary mb-1 block uppercase">Target (e.g. 10Y)</label><input className="input-field w-full" placeholder="CUSIP or Ticker" value={newAlert.target} onChange={e => setNewAlert({...newAlert, target: e.target.value})} /></div>
              <div><label className="text-xs text-text-secondary mb-1 block uppercase">Condition</label><select className="input-field w-full" value={newAlert.condition} onChange={e => setNewAlert({...newAlert, condition: e.target.value})}><option value="above">Rises Above</option><option value="below">Falls Below</option></select></div>
              <div><label className="text-xs text-text-secondary mb-1 block uppercase">Threshold (%)</label><input className="input-field w-full" type="number" step="0.01" placeholder="4.00" value={newAlert.threshold} onChange={e => setNewAlert({...newAlert, threshold: e.target.value})} /></div>
            </div>
            <div className="px-4 pb-4 flex justify-end gap-2">
              <button className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleCreate}>Activate Monitoring</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Active Alerts */}
        <div className="panel bg-black">
          <div className="panel-header"><div className="flex items-center gap-2"><Bell className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">Active Monitoring Jobs</span></div><span className="badge-accent">{alerts.length}</span></div>
          <div className="divide-y divide-border/50">
            {alerts.length === 0 ? (
              <div className="p-8 text-center text-xs text-text-tertiary">No active alerts configured.</div>
            ) : alerts.map((a, i) => (
              <div key={i} className="px-4 py-3 flex items-center justify-between hover:bg-bg-hover transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-accent/10 flex items-center justify-center text-accent">{ALERT_TYPES.find(t => t.value === a.type)?.icon}</div>
                  <div><div className="text-xs font-medium">{a.target}</div><div className="text-[10px] text-text-tertiary uppercase tracking-tighter">{a.condition} {a.threshold}%</div></div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-positive/10 text-positive text-[10px] font-bold border border-positive/20">
                    <div className="w-1 h-1 rounded-full bg-positive animate-pulse" /> MONITORING
                  </div>
                  <button onClick={() => handleDelete(a._id)} className="p-1 text-text-tertiary hover:text-negative transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Triggered Alerts */}
        <div className="panel bg-black">
          <div className="panel-header"><div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-warning" /><span className="text-sm font-semibold">Triggered History</span></div></div>
          <div className="divide-y divide-border/50">
            {triggered.length === 0 ? (
              <div className="p-8 text-center text-xs text-text-tertiary">No recently triggered alerts.</div>
            ) : triggered.map((t, i) => (
              <div key={i} className={`px-4 py-3 flex items-center gap-3 hover:bg-bg-hover transition-colors ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                <div className={`w-2 h-2 rounded-full shrink-0 ${t.type === 'yield_change' ? 'bg-accent' : 'bg-warning'}`} />
                <div className="flex-1">
                  <div className="text-xs font-medium">{t.target} {t.condition} {t.threshold}% triggered</div>
                  <div className="text-[10px] text-text-tertiary">{new Date(t.triggered_at).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
