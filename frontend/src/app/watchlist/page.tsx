'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, Plus, Bell, Trash2, X } from 'lucide-react';

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [availableBonds, setAvailableBonds] = useState<any[]>([]);
  const [selectedBondId, setSelectedBondId] = useState('');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  const fetchWatchlist = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/watchlist/`);
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.data.length > 0) {
          setWatchlist(json.data[0]);
        } else if (json.success && json.data.length === 0) {
          // Create default watchlist
          const createRes = await fetch(`${API_URL}/api/v1/watchlist/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'Rate Movers Watch' })
          });
          const createJson = await createRes.json();
          if (createJson.success) setWatchlist(createJson.data);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  const fetchBonds = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/screener/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 100 })
      });
      if (res.ok) {
        const json = await res.json();
        if (json.success) setAvailableBonds(json.data.bonds);
      }
    } catch (e) {
      console.error(e);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchWatchlist();
    fetchBonds();
  }, [fetchWatchlist, fetchBonds]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!watchlist || !selectedBondId) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/watchlist/${watchlist._id}/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bond_id: selectedBondId })
      });
      if (res.ok) {
        setShowAddModal(false);
        setSelectedBondId('');
        fetchWatchlist();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemove = async (bondId: string) => {
    if (!watchlist) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/watchlist/${watchlist._id}/remove/${bondId}`, {
        method: 'DELETE'
      });
      if (res.ok) fetchWatchlist();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
        <div className="text-sm text-text-secondary font-mono">Loading Watchlist...</div>
      </div>
    </div>
  );

  const bonds = watchlist?.enriched_bonds || [];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">Watchlist</h1>
        <div className="flex gap-2"><button onClick={() => setShowAddModal(true)} className="btn-primary flex items-center gap-1"><Plus className="w-4 h-4" />Add Bond</button></div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2"><Eye className="w-4 h-4 text-accent" /><span className="text-sm font-semibold">{watchlist?.name || 'Watchlist'}</span></div>
          <span className="text-xs text-text-tertiary">{bonds.length} bonds</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr>
              <th className="table-header">Bond</th><th className="table-header">Type</th><th className="table-header text-right">YTM</th><th className="table-header text-right">Price</th><th className="table-header text-right">Change</th><th className="table-header">Added</th><th className="table-header text-right">Actions</th>
            </tr></thead>
            <tbody>{bonds.length === 0 ? (
              <tr><td colSpan={7} className="text-center p-8 text-text-tertiary">No bonds in watchlist.</td></tr>
            ) : bonds.map((item: any, i: number) => {
              const b = item.bond;
              if (!b) return null;
              // Mocking a change value for visual demo if not available
              const change = b.change || 0;
              return (
              <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                <td className="table-cell text-xs font-medium max-w-[220px] truncate">{b.issuer} {b.coupon_rate}%</td>
                <td className="table-cell"><span className="badge-accent text-[10px]">{b.type}</span></td>
                <td className="table-cell text-right font-mono text-accent font-semibold">{b.coupon_rate?.toFixed(2)}%</td>
                <td className="table-cell text-right font-mono">{b.price?.toFixed(2)}</td>
                <td className={`table-cell text-right font-mono ${change > 0 ? 'text-positive' : change < 0 ? 'text-negative' : 'text-text-tertiary'}`}>{change > 0 ? '+' : ''}{change.toFixed(3)}</td>
                <td className="table-cell text-xs text-text-secondary">{new Date(item.added_at).toLocaleDateString()}</td>
                <td className="table-cell text-right">
                  <div className="flex gap-1 justify-end">
                    <button className="p-1 text-text-tertiary hover:text-accent transition-colors"><Bell className="w-3.5 h-3.5" /></button>
                    <button onClick={() => handleRemove(b._id)} className="p-1 text-text-tertiary hover:text-negative transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                </td>
              </tr>
            )})}</tbody>
          </table>
        </div>
      </div>

      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setShowAddModal(false)} />
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="panel w-full max-w-md bg-black relative z-10 border-accent/30">
              <div className="panel-header">
                <div className="flex items-center gap-2 text-accent">
                  <Eye className="w-4 h-4" />
                  <span className="text-sm font-bold">Add to Watchlist</span>
                </div>
                <button onClick={() => setShowAddModal(false)} className="text-text-tertiary hover:text-text"><X className="w-4 h-4" /></button>
              </div>
              <form onSubmit={handleAdd} className="p-4 space-y-4">
                <div>
                  <label className="text-xs text-text-secondary mb-1 block uppercase tracking-wider">Select Bond</label>
                  <select required className="input-field w-full" value={selectedBondId} onChange={e => setSelectedBondId(e.target.value)}>
                    <option value="">Select a bond from market...</option>
                    {availableBonds.map(b => <option key={b._id} value={b._id}>{b.issuer} — {b.type.toUpperCase()} ({b.coupon_rate}%)</option>)}
                  </select>
                </div>
                <div className="flex gap-2 pt-2">
                  <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary flex-1">Cancel</button>
                  <button type="submit" className="btn-primary flex-1">Add to Watchlist</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
