'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, SlidersHorizontal, ChevronLeft, ChevronRight, Plus, X, Info } from 'lucide-react';

const MOCK_BONDS = Array.from({ length: 25 }, (_, i) => ({
  id: `bond_${i}`,
  name: [`Apple Inc. 3.750%`, `Microsoft 4.200%`, `U.S. Treasury 10Y`, `Goldman Sachs 5.100%`, `California GO 3.500%`, `Tesla 5.875%`, `JPMorgan 4.650%`, `Amazon 3.900%`, `Ford Motor 6.200%`, `Alphabet 3.375%`][i % 10] + ` ${2026 + (i % 10)}`,
  type: ['corporate', 'corporate', 'treasury', 'corporate', 'municipal', 'corporate', 'corporate', 'corporate', 'corporate', 'corporate'][i % 10],
  rating: ['AA+', 'AAA', 'AAA', 'A+', 'AA', 'BBB-', 'A+', 'AA', 'BB+', 'AA+'][i % 10],
  coupon: [3.75, 4.20, 4.25, 5.10, 3.50, 5.875, 4.65, 3.90, 6.20, 3.375][i % 10],
  maturity: `${2026 + (i % 15)}-${String((i % 12) + 1).padStart(2, '0')}-15`,
  price: [102.30, 99.80, 98.50, 97.20, 104.10, 93.50, 101.40, 103.20, 88.75, 105.60][i % 10],
  ytm: [3.42, 4.25, 4.45, 5.55, 3.12, 6.85, 4.50, 3.65, 7.80, 3.05][i % 10],
  duration: [4.2, 6.8, 8.5, 5.3, 12.1, 3.8, 7.2, 9.4, 2.9, 10.5][i % 10],
  spread: [45, 55, 0, 120, 35, 250, 85, 40, 345, 30][i % 10],
  risk: [25, 20, 10, 45, 30, 72, 40, 22, 80, 18][i % 10],
}));

export default function ScreenerPage() {
  const [bonds, setBonds] = useState(MOCK_BONDS);
  const [filters, setFilters] = useState({ type: '', rating: '', minYtm: '', maxYtm: '', sector: '', search: '' });
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('ytm');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [intelligence, setIntelligence] = useState<any>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsAddSubmitting] = useState(false);
  const [newBond, setNewBond] = useState({
    issuer: '', cusip: '', type: 'corporate', coupon_rate: 5.0, maturity_date: '2030-01-01', price: 100.0, rating: 'A'
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  const fetchBonds = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/screener/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page, limit: 25, sort_by: sortBy, sort_order: sortDir, ...filters }),
      });
      if (res.ok) {
        const json = await res.json();
        if (json.data?.bonds?.length) setBonds(json.data.bonds);
        if (json.data?.intelligence) setIntelligence(json.data.intelligence);
        else setIntelligence(null);
      }
    } catch (e) {
      console.error("Screener fetch error:", e);
    }
  }, [API_URL, page, sortBy, sortDir, filters]);

  useEffect(() => {
    fetchBonds();
  }, [fetchBonds]);

  const handleAddBond = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAddSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/bonds/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBond),
      });
      if (res.ok) {
        setShowAddModal(false);
        setNewBond({ issuer: '', cusip: '', type: 'corporate', coupon_rate: 5.0, maturity_date: '2030-01-01', price: 100.0, rating: 'A' });
        fetchBonds();
      }
    } catch (err) {
      alert("Terminal error: Failed to register bond in database.");
    } finally {
      setIsAddSubmitting(false);
    }
  };

  const handleApplyFilters = () => {
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilters({ type: '', rating: '', minYtm: '', maxYtm: '', sector: '', search: '' });
    setPage(1);
  };

  const ratingColor = (r: string) => {
    if (r.startsWith('AAA')) return 'text-positive';
    if (r.startsWith('AA')) return 'text-positive';
    if (r.startsWith('A')) return 'text-blueAccent';
    if (r.startsWith('BBB')) return 'text-warning';
    return 'text-negative';
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 h-[calc(100vh-7rem)]">
      {/* Filter Sidebar */}
      <div className="w-64 shrink-0 panel overflow-y-auto bg-black">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold uppercase tracking-tight">Terminal Filters</span>
          </div>
        </div>
        <div className="p-3 space-y-4">
          <button onClick={() => setShowAddModal(true)} className="btn-primary w-full flex items-center justify-center gap-2 text-xs py-2 mb-2">
            <Plus className="w-3.5 h-3.5" /> Register New Bond
          </button>
          
          <div>
            <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Search Issuer</label>
            <input className="input-field w-full" placeholder="e.g. Apple" value={filters.search} onChange={e => setFilters({...filters, search: e.target.value})} />
          </div>
          <div>
            <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Asset Class</label>
            <select className="input-field w-full" value={filters.type} onChange={e => setFilters({...filters, type: e.target.value})}>
              <option value="">All Securities</option>
              <option value="treasury">Treasury</option>
              <option value="corporate">Corporate</option>
              <option value="municipal">Municipal</option>
              <option value="tips">TIPS</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Credit Rating</label>
            <select className="input-field w-full" value={filters.rating} onChange={e => setFilters({...filters, rating: e.target.value})}>
              <option value="">All Ratings</option>
              {['AAA','AA+','AA','AA-','A+','A','A-','BBB+','BBB','BBB-','BB+','BB','B+','B','CCC'].map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Min YTM</label>
              <input className="input-field w-full" type="number" step="0.1" placeholder="0" value={filters.minYtm} onChange={e => setFilters({...filters, minYtm: e.target.value})} />
            </div>
            <div>
              <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Max YTM</label>
              <input className="input-field w-full" type="number" step="0.1" placeholder="15" value={filters.maxYtm} onChange={e => setFilters({...filters, maxYtm: e.target.value})} />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary flex-1 text-center py-1.5" onClick={handleApplyFilters}>Query</button>
            <button className="btn-secondary flex-1 text-center py-1.5" onClick={handleResetFilters}>Clear</button>
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        <AnimatePresence>
          {intelligence?.ai_insight && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="panel bg-accent/5 border-accent/20 p-4">
              <div className="flex items-center gap-2 mb-2 text-accent">
                <Info className="w-4 h-4" />
                <span className="text-xs font-black uppercase tracking-tight">Terminal Intelligence — {intelligence.related_issuer}</span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed font-mono italic"><q>{intelligence.ai_insight}</q></p>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex-1 panel flex flex-col min-w-0 bg-black">
        <div className="panel-header">
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold text-accent uppercase tracking-tight">Market Universe</span>
            <div className="h-4 w-[1px] bg-border" />
            <span className="text-[10px] text-text-tertiary font-mono uppercase">{bonds.length} Instruments Loaded</span>
          </div>
        </div>
        <div className="flex-1 overflow-auto">
          <table className="w-full">
            <thead className="sticky top-0 z-10">
              <tr>
                <th className="table-header">Issuer / Security</th>
                <th className="table-header">Type</th>
                <th className="table-header">Rating</th>
                <th className="table-header text-right">Coupon</th>
                <th className="table-header text-right">Price</th>
                <th className="table-header text-right">YTM</th>
                <th className="table-header text-right">Duration</th>
                <th className="table-header text-right">Risk</th>
              </tr>
            </thead>
            <tbody>
              {bonds.map((b, i) => (
                <tr key={i} className={`table-row ${i % 2 === 1 ? 'table-row-alt' : ''}`}>
                  <td className="table-cell text-xs font-bold text-text max-w-[200px] truncate">{b.name || (b as any).issuer}</td>
                  <td className="table-cell"><span className="badge-accent text-[9px] uppercase font-bold px-1.5">{b.type}</span></td>
                  <td className={`table-cell font-mono font-bold text-xs ${ratingColor(b.rating)}`}>{b.rating}</td>
                  <td className="table-cell text-right font-mono text-xs">{b.coupon?.toFixed(3)}%</td>
                  <td className="table-cell text-right font-mono text-xs">{b.price?.toFixed(2)}</td>
                  <td className="table-cell text-right font-mono text-xs text-accent font-bold">{b.ytm?.toFixed(2)}%</td>
                  <td className="table-cell text-right font-mono text-xs">{b.duration?.toFixed(1)}y</td>
                  <td className="table-cell text-right">
                    <span className={`font-mono text-[10px] font-black px-1.5 py-0.5 rounded ${b.risk < 30 ? 'bg-positive/10 text-positive' : b.risk < 60 ? 'bg-warning/10 text-warning' : 'bg-negative/10 text-negative'}`}>{b.risk}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-2 border-t border-border flex items-center justify-between">
          <span className="text-[10px] text-text-tertiary font-mono uppercase">Page {page} of terminal session</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(Math.max(1, page - 1))} className="btn-secondary flex items-center gap-1 text-[10px] py-1 px-2 uppercase font-bold"><ChevronLeft className="w-3 h-3" />Prev</button>
            <button onClick={() => setPage(page + 1)} className="btn-secondary flex items-center gap-1 text-[10px] py-1 px-2 uppercase font-bold">Next<ChevronRight className="w-3 h-3" /></button>
          </div>
        </div>
      </div>
    </div>

      {/* Add Bond Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/90 backdrop-blur-md" onClick={() => setShowAddModal(false)} />
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="panel w-full max-w-lg bg-black relative z-10 border-accent/40 shadow-2xl shadow-accent/10">
              <div className="panel-header bg-accent/5">
                <div className="flex items-center gap-2 text-accent">
                  <Plus className="w-4 h-4" />
                  <span className="text-sm font-black uppercase tracking-tight">Security Registration</span>
                </div>
                <button onClick={() => setShowAddModal(false)} className="text-text-tertiary hover:text-text"><X className="w-4 h-4" /></button>
              </div>
              <form onSubmit={handleAddBond} className="p-5 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Issuer Name</label>
                    <input required className="input-field w-full" placeholder="e.g. Goldman Sachs Group Inc" value={newBond.issuer} onChange={e => setNewBond({...newBond, issuer: e.target.value})} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">CUSIP / Symbol</label>
                    <input required className="input-field w-full font-mono" placeholder="9-digit ID" value={newBond.cusip} onChange={e => setNewBond({...newBond, cusip: e.target.value})} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Asset Type</label>
                    <select className="input-field w-full" value={newBond.type} onChange={e => setNewBond({...newBond, type: e.target.value})}>
                      <option value="corporate">Corporate</option>
                      <option value="treasury">Treasury</option>
                      <option value="municipal">Municipal</option>
                      <option value="tips">TIPS</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Coupon (%)</label>
                    <input required type="number" step="0.001" className="input-field w-full font-mono" value={newBond.coupon_rate} onChange={e => setNewBond({...newBond, coupon_rate: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Maturity Date</label>
                    <input required type="date" className="input-field w-full font-mono" value={newBond.maturity_date} onChange={e => setNewBond({...newBond, maturity_date: e.target.value})} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">Initial Price ($)</label>
                    <input required type="number" step="0.01" className="input-field w-full font-mono" value={newBond.price} onChange={e => setNewBond({...newBond, price: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary mb-1 block uppercase font-bold">S&P Rating</label>
                    <select className="input-field w-full font-mono" value={newBond.rating} onChange={e => setNewBond({...newBond, rating: e.target.value})}>
                      {['AAA','AA+','AA','AA-','A+','A','A-','BBB+','BBB','BBB-','BB+','BB','B+','B','CCC','D','NR'].map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                </div>
                <div className="bg-bg-panel/50 p-3 rounded border border-border flex gap-3">
                  <Info className="w-4 h-4 text-blueAccent shrink-0 mt-0.5" />
                  <p className="text-[10px] text-text-tertiary leading-relaxed uppercase">Registered securities are immediately indexed for terminal-wide search and portfolio inclusion.</p>
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary flex-1 uppercase font-bold py-2">Discard</button>
                  <button type="submit" disabled={isSubmitting} className="btn-primary flex-1 uppercase font-bold py-2 shadow-lg shadow-accent/20 disabled:opacity-50">
                    {isSubmitting ? 'Registering...' : 'Confirm Registration'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
