'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Plus, DollarSign, TrendingUp, Clock, Shield, Trash2, X, AlertCircle } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

interface Holding {
  _id?: string;
  bond_id: string;
  name: string;
  type: string;
  qty: number;
  avgPrice: number;
  current: number;
  pnl: number;
  weight: number;
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [portfolioId, setPortfolioId] = useState<string | null>(null);
  const [summary, setSummary] = useState<any>(null);
  
  // Form State
  const [formData, setFormData] = useState({
    bond_id: '',
    quantity: 1,
    avg_price: 100
  });

  const [availableBonds, setAvailableBonds] = useState<any[]>([]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fetchBonds = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/screener/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 100 })
      });
      if (!res.ok) throw new Error('Network response was not ok');
      const json = await res.json();
      if (json.success) setAvailableBonds(json.data.bonds);
    } catch (e) {
      console.error("Failed to fetch bonds", e);
    }
  }, [API_URL]);

  const fetchPortfolio = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/portfolio/`);
      if (!res.ok) throw new Error('Network response was not ok');
      const json = await res.json();

      if (json.success && json.data.length > 0) {
        const pid = json.data[0]._id;
        setPortfolioId(pid);
        const detailRes = await fetch(`${API_URL}/api/v1/portfolio/${pid}`);
        if (!detailRes.ok) throw new Error('Network response was not ok');
        const detailJson = await detailRes.json();

        if (detailJson.success) {
          const enriched = detailJson.data.enriched_holdings.map((h: any) => ({
            _id: h.bond_id,
            bond_id: h.bond_id,
            name: h.bond?.issuer || 'Unknown Bond',
            type: h.bond?.type || 'corporate',
            qty: h.quantity,
            avgPrice: h.avg_price,
            current: h.bond?.price || 100,
            pnl: h.pnl,
            weight: 0
          }));

          const totalValue = enriched.reduce((s: number, h: any) => s + (h.current * h.qty), 0);
          const finalHoldings = enriched.map((h: any) => ({
            ...h,
            weight: totalValue > 0 ? Math.round(((h.current * h.qty) / totalValue) * 100) : 0
          }));

          setHoldings(finalHoldings);
          setSummary(detailJson.data.summary);
        }
      } else if (json.success && json.data.length === 0) {
        const createRes = await fetch(`${API_URL}/api/v1/portfolio/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Default Portfolio' })
        });
        if (!createRes.ok) throw new Error('Network response was not ok');
        const createJson = await createRes.json();
        if (createJson.success) setPortfolioId(createJson.data._id);
      }
    } catch (e) {
      console.error("Failed to fetch portfolio", e);
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchPortfolio();
    fetchBonds();
  }, [fetchBonds, fetchPortfolio]);

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!portfolioId) return;

    try {
      const res = await fetch(`${API_URL}/api/v1/portfolio/${portfolioId}/holdings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error('Network response was not ok');
      const json = await res.json();
      if (json.success) {
        setShowModal(false);
        setFormData({ bond_id: '', quantity: 1, avg_price: 100 });
        fetchPortfolio();
      }
    } catch (e) {
      alert("Error adding holding");
    }
  };

  const handleDelete = async (bondId: string) => {
    if (!portfolioId) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/portfolio/${portfolioId}/holdings/${bondId}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Network response was not ok');
      if ((await res.json()).success) fetchPortfolio();
    } catch (e) {
      alert("Error deleting holding");
    }
  };

  const totalValue = summary?.total_value || 0;
  const totalPnl = holdings.reduce((s, h) => s + h.pnl, 0);

  const typeData = Array.from(new Set(holdings.map(h => h.type))).map(type => ({
    name: type.charAt(0).toUpperCase() + type.slice(1),
    value: Math.round(holdings.filter(h => h.type === type).reduce((s, h) => s + h.weight, 0)),
    color: type === 'treasury' ? '#2563EB' : type === 'corporate' ? '#3B82F6' : '#38BDF8'
  }));

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
        <div className="text-sm text-text-secondary font-mono">Syncing Portfolio with Terminal...</div>
      </div>
    </div>
  );

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">Portfolio Manager</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-1"><Plus className="w-4 h-4" />Add Holding</button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Total Value', value: `$${(totalValue).toLocaleString()}`, icon: <DollarSign className="w-4 h-4" />, color: 'text-accent' },
          { label: 'Total P&L', value: `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(0)}`, icon: <TrendingUp className="w-4 h-4" />, color: totalPnl >= 0 ? 'text-positive' : 'text-negative' },
          { label: 'Avg YTM', value: summary?.avg_ytm ? `${summary.avg_ytm}%` : '—', icon: <TrendingUp className="w-4 h-4" />, color: 'text-accent' },
          { label: 'Avg Duration', value: summary?.avg_duration ? `${summary.avg_duration}y` : '—', icon: <Clock className="w-4 h-4" />, color: 'text-blueAccent' },
          { label: 'Risk Score', value: holdings.length ? '32/100' : '—', icon: <Shield className="w-4 h-4" />, color: 'text-positive' },
        ].map((m, i) => (
          <div key={i} className="panel p-3 card-hover bg-black">
            <div className="flex items-center gap-1 text-text-secondary mb-1">{m.icon}<span className="text-[10px] uppercase">{m.label}</span></div>
            <div className={`font-mono text-lg font-bold ${m.color}`}>{m.value}</div>
          </div>
        ))}
      </div>

      {holdings.length === 0 ? (
        <div className="panel p-12 flex flex-col items-center justify-center text-center bg-black border-dashed border-2">
          <Briefcase className="w-12 h-12 text-text-tertiary mb-4 opacity-20" />
          <h2 className="text-lg font-bold mb-2">No Holdings Found</h2>
          <p className="text-sm text-text-secondary max-w-xs mb-6">Your portfolio is currently empty. Add your first bond position to start tracking performance.</p>
          <button onClick={() => setShowModal(true)} className="btn-primary">Initialize Portfolio</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Holdings Table */}
          <div className="panel lg:col-span-2 bg-black">
            <div className="panel-header"><span className="text-sm font-semibold">Holdings</span><span className="text-xs text-text-tertiary">{holdings.length} positions</span></div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr><th className="table-header">Bond</th><th className="table-header text-right">Qty</th><th className="table-header text-right">Avg Price</th><th className="table-header text-right">Current</th><th className="table-header text-right">P&L</th><th className="table-header text-right">Action</th></tr></thead>
                <tbody>{holdings.map((h, i) => (
                  <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                    <td className="table-cell"><div className="text-xs font-medium truncate max-w-[200px]">{h.name}</div><div className="text-[10px] text-text-tertiary">{h.type}</div></td>
                    <td className="table-cell text-right font-mono">{h.qty}</td>
                    <td className="table-cell text-right font-mono">{h.avgPrice.toFixed(2)}</td>
                    <td className="table-cell text-right font-mono">{h.current.toFixed(2)}</td>
                    <td className={`table-cell text-right font-mono font-semibold ${h.pnl >= 0 ? 'text-positive' : 'text-negative'}`}>{h.pnl >= 0 ? '+' : ''}${h.pnl.toFixed(0)}</td>
                    <td className="table-cell text-right">
                      <button onClick={() => handleDelete(h.bond_id)} className="p-1 text-text-tertiary hover:text-negative transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </div>

          {/* Allocation Charts */}
          <div className="space-y-4">
            <div className="panel bg-black">
              <div className="panel-header"><span className="text-sm font-semibold">Allocation — By Type</span></div>
              <div className="p-3">
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie data={typeData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value" stroke="#000" strokeWidth={2}>
                      {typeData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #30363D', borderRadius: 8, color: '#F8FAFC', fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap gap-2 justify-center">
                  {typeData.map((d, i) => <div key={i} className="flex items-center gap-1 text-[10px]"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} /><span className="text-text-secondary">{d.name} {d.value}%</span></div>)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Holding Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setShowModal(false)} />
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="panel w-full max-w-md bg-black relative z-10 border-accent/30">
              <div className="panel-header">
                <div className="flex items-center gap-2 text-accent">
                  <Briefcase className="w-4 h-4" />
                  <span className="text-sm font-bold">Add Holding to Portfolio</span>
                </div>
                <button onClick={() => setShowModal(false)} className="text-text-tertiary hover:text-text"><X className="w-4 h-4" /></button>
              </div>
              <form onSubmit={handleAddHolding} className="p-4 space-y-4">
                <div>
                  <label className="text-xs text-text-secondary mb-1 block uppercase tracking-wider">Select Bond</label>
                  <select required className="input-field w-full" value={formData.bond_id} onChange={e => setFormData({...formData, bond_id: e.target.value})}>
                    <option value="">Select a bond from market...</option>
                    {availableBonds.map(b => <option key={b._id} value={b._id}>{b.issuer} — {b.type.toUpperCase()} ({b.coupon_rate}% {new Date(b.maturity_date).getFullYear()})</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-text-secondary mb-1 block uppercase tracking-wider">Quantity</label>
                    <input required type="number" min="1" className="input-field w-full" value={formData.quantity} onChange={e => setFormData({...formData, quantity: parseInt(e.target.value) || 0})} />
                  </div>
                  <div>
                    <label className="text-xs text-text-secondary mb-1 block uppercase tracking-wider">Avg Price ($)</label>
                    <input required type="number" step="0.01" className="input-field w-full" value={formData.avg_price} onChange={e => setFormData({...formData, avg_price: parseFloat(e.target.value) || 0})} />
                  </div>
                </div>
                <div className="bg-accent/5 p-3 rounded border border-accent/20 flex gap-3">
                  <AlertCircle className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <p className="text-[10px] text-text-secondary leading-relaxed">Ensure CUSIP and purchase details match your brokerage statement for accurate risk analysis.</p>
                </div>
                <div className="flex gap-2 pt-2">
                  <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1">Cancel</button>
                  <button type="submit" className="btn-primary flex-1">Add Holding</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
