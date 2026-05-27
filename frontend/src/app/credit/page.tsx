'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Search, Building2, TrendingUp, Cpu, Landmark,
  BarChart3, Activity, AlertTriangle, FileText, Play, CheckCircle2,
  HelpCircle, Users, Globe2, Wallet, Layers, ArrowUpRight, Check
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, Cell, PieChart, Pie, AreaChart, Area, Legend
} from 'recharts';

export default function CreditPage() {
  const [issuers, setIssuers] = useState<any[]>([]);
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [searchQuery, setSearchQuery] = useState('');
  const [data, setData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Scenario stress simulation states
  const [selectedScenario, setSelectedScenario] = useState('recession');

  // Memo states
  const [memo, setMemo] = useState('');
  const [memoLoading, setMemoLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  // Fetch Available Issuers
  useEffect(() => {
    async function loadIssuers() {
      try {
        const res = await fetch(`${API_URL}/api/v1/credit/issuers`);
        if (res.ok) {
          const json = await res.json();
          if (json.success) {
            setIssuers(json.data);
            if (json.data.length > 0) {
              setSelectedTicker(json.data[0].ticker);
            }
          }
        }
      } catch (e) {
        console.error('Failed to load issuers:', e);
      }
    }
    loadIssuers();
  }, [API_URL]);

  // Fetch Full Credit Profile details
  useEffect(() => {
    async function loadCreditProfile() {
      if (!selectedTicker) return;
      setLoading(true);
      setMemo(''); // Reset memo on company change
      try {
        const res = await fetch(`${API_URL}/api/v1/credit/issuer/${selectedTicker}`);
        if (res.ok) {
          const json = await res.json();
          if (json.success) {
            setData(json.data);
          }
        }
      } catch (e) {
        console.error('Failed to load credit profile:', e);
      } finally {
        setLoading(false);
      }
    }
    loadCreditProfile();
  }, [selectedTicker, API_URL]);

  // Generate Institutional Credit Memo
  const generateMemo = async () => {
    if (!selectedTicker) return;
    setMemoLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/credit/memo/${selectedTicker}`, {
        method: 'POST'
      });
      if (res.ok) {
        const json = await res.json();
        if (json.success) {
          setMemo(json.memo);
        }
      }
    } catch (e) {
      console.error('Failed to generate memo:', e);
    } finally {
      setMemoLoading(false);
    }
  };

  const getOutlookColor = (o: string) => {
    if (o === 'Positive') return 'text-positive border-positive/30 bg-positive/10';
    if (o === 'Stable') return 'text-secondary border-secondary/30 bg-secondary/10';
    return 'text-negative border-negative/30 bg-negative/10';
  };

  const getZScoreColor = (z: number) => {
    if (z > 2.9) return 'text-positive';
    if (z > 1.2) return 'text-warning';
    return 'text-negative';
  };

  if (loading && !data) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-text-tertiary font-mono">RETRIEVING INSTITUTIONAL CREDIT LEDGER...</p>
        </div>
      </div>
    );
  }

  const p = data?.analysis?.profile || {};
  const d = data?.analysis?.debt_structure || {};
  const l = data?.analysis?.liquidity || {};
  const le = data?.analysis?.leverage || {};
  const pr = data?.analysis?.profitability || {};
  const r = data?.analysis?.quant_risk || {};
  const ra = data?.analysis?.ratings || {};
  const m = data?.analysis?.market_analysis || {};
  const stress = data?.analysis?.scenarios || {};
  const events = data?.analysis?.events || [];
  const peers = data?.peers || [];
  const history5y = data?.analysis?.financial_history_5y || {};

  // Formats maturity ladder data for Recharts
  const maturityChartData = d.maturity_ladder
    ? Object.entries(d.maturity_ladder).map(([year, val]: any) => ({
      name: year === '30' ? '30Y+' : `${year}Y`,
      Maturity: val,
    }))
    : [];

  // Formats historical 5Y revenue/debt data for Recharts
  const historyChartData = history5y.years
    ? history5y.years.map((year: number, idx: number) => ({
      year: year.toString(),
      Revenue: history5y.revenue[idx],
      Debt: history5y.lt_debt[idx] + history5y.st_debt[idx],
      Cash: history5y.cash[idx],
    }))
    : [];

  const activeScenario = stress[selectedScenario] || {};

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {/* Page Title */}
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <div>
          <h1 className="text-lg font-bold text-text">Credit Intelligence</h1>
          <p className="text-xs text-text-tertiary">Institutional credit research, leverage profiles, and default risk modeling</p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-text-tertiary bg-bg-panel border border-border px-3 py-1 rounded font-mono">
          <Shield className="w-4 h-4 text-accent" />
          <span>VERIFIED BY MOODY'S & S&P</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left Side: Issuer Selector */}
        <div className="panel flex flex-col h-[75vh]">
          <div className="panel-header flex items-center gap-2">
            <Search className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold">Issuer Search</span>
          </div>
          <div className="p-3 border-b border-border/60">
            <input
              className="input-field w-full text-xs"
              placeholder="Search corporate ticker..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {issuers
              .filter((i) =>
                i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                i.ticker.toLowerCase().includes(searchQuery.toLowerCase())
              )
              .map((issuer) => (
                <button
                  key={issuer.ticker}
                  onClick={() => setSelectedTicker(issuer.ticker)}
                  className={`w-full text-left px-3 py-2.5 rounded transition-all flex items-center justify-between border ${selectedTicker === issuer.ticker
                      ? 'bg-accent/10 text-accent border-accent/30 shadow-md'
                      : 'hover:bg-bg-hover text-text-secondary border-transparent'
                    }`}
                >
                  <div>
                    <div className="font-semibold text-xs text-text">{issuer.name}</div>
                    <div className="text-[10px] text-text-tertiary uppercase font-mono mt-0.5">{issuer.sector}</div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-accent">{issuer.ticker}</span>
                    <div className="text-[9px] text-positive font-mono font-semibold mt-0.5">{issuer.rating}</div>
                  </div>
                </button>
              ))}
          </div>
        </div>

        {/* Right Side: Analytical Workspace */}
        <div className="lg:col-span-3 space-y-4">
          {/* Header Summary Panel */}
          <div className="panel bg-[#0B0B0B] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-accent">
            <div>
              <div className="flex items-center gap-3">
                <span className="text-lg font-black text-text">{p.name}</span>
                <span className="bg-accent/10 border border-accent/20 px-2 py-0.5 rounded text-[10px] font-mono text-accent font-bold">
                  {p.ticker}
                </span>
                <span className="bg-bg-panel border border-border px-2 py-0.5 rounded text-[10px] font-mono text-text-secondary">
                  CUSIP: {p.cusip}
                </span>
              </div>
              <p className="text-xs text-text-tertiary mt-1 font-mono">
                {p.industry} • {p.hq}
              </p>
            </div>

            {/* Quick Badges */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="bg-bg-panel border border-border rounded px-3 py-1 text-center">
                <div className="text-[9px] text-text-tertiary uppercase">S&P / Moody's</div>
                <div className="font-mono text-xs font-bold mt-0.5 text-text flex items-center gap-1.5 justify-center">
                  <span className="text-positive">{ra.sp}</span>
                  <span className="text-text-tertiary">/</span>
                  <span className="text-accent">{ra.moodys}</span>
                </div>
              </div>
              <div className={`border rounded px-3 py-1 text-center ${getOutlookColor(ra.outlook)}`}>
                <div className="text-[9px] uppercase opacity-75">Outlook</div>
                <div className="font-mono text-xs font-bold mt-0.5 uppercase">{ra.outlook}</div>
              </div>
              <div className="bg-bg-panel border border-border rounded px-3 py-1 text-center">
                <div className="text-[9px] text-text-tertiary uppercase">Risk Grade</div>
                <div className="font-mono text-xs font-bold mt-0.5 text-accent flex items-center justify-center uppercase font-mono">
                  {r.risk_grade}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-border/80 gap-1 overflow-x-auto scrollbar-hide">
            {[
              { id: 'overview', label: 'Issuer Profile', icon: Building2 },
              { id: 'solvency', label: 'Solvency & Risk', icon: Shield },
              { id: 'debt', label: 'Debt Ladder', icon: Layers },
              { id: 'ratios', label: 'Financials & Peers', icon: BarChart3 },
              { id: 'scenarios', label: 'Stress Calculator', icon: Play },
              { id: 'memo', label: 'AI Credit Memo', icon: FileText },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${activeTab === tab.id
                      ? 'border-accent text-accent bg-accent/5'
                      : 'border-transparent text-text-secondary hover:text-text hover:bg-bg-hover'
                    }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Contents */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.15 }}
              className="space-y-4"
            >
              {/* 1. Overview Tab */}
              {activeTab === 'overview' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Left Column: Business & Segments */}
                  <div className="panel md:col-span-2 space-y-4 p-4">
                    <div className="space-y-2">
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider">Business Description</h3>
                      <p className="text-xs text-text-secondary leading-relaxed font-mono">{p.business_description}</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-border/40 pt-4">
                      {/* Segment Breakdown */}
                      <div>
                        <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-2">Business Segments</h4>
                        <div className="space-y-1.5">
                          {p.segments?.map((seg: any, i: number) => (
                            <div key={i} className="flex items-center justify-between text-xs font-mono">
                              <span className="text-text-secondary">{seg.name}</span>
                              <span className="font-bold text-text">{seg.pct}%</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Geographic Distribution */}
                      <div>
                        <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-2">Geographic Distribution</h4>
                        <div className="space-y-1.5">
                          {p.geographic_distribution?.map((g: any, i: number) => (
                            <div key={i} className="flex items-center justify-between text-xs font-mono">
                              <span className="text-text-secondary">{g.region}</span>
                              <span className="font-bold text-text">{g.pct}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Governance & Ownership */}
                  <div className="panel p-4 space-y-4">
                    <div>
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Users className="w-4 h-4" /> Management Team
                      </h3>
                      <div className="space-y-2 font-mono text-xs">
                        {p.management?.map((m: any, i: number) => (
                          <div key={i} className="border-b border-border/20 pb-1 last:border-0">
                            <div className="font-semibold text-text">{m.name}</div>
                            <div className="text-[10px] text-text-tertiary">{m.title}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="border-t border-border/40 pt-4 space-y-3">
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Globe2 className="w-4 h-4" /> Capital Structure & Ownership
                      </h3>
                      <div className="space-y-1.5 text-xs font-mono">
                        <div className="flex justify-between">
                          <span className="text-text-secondary">Institutional Ownership</span>
                          <span className="text-text font-bold">{p.ownership?.institutional}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">Insider Ownership</span>
                          <span className="text-text font-bold">{p.ownership?.insider}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">Retail Ownership</span>
                          <span className="text-text font-bold">{p.ownership?.retail}%</span>
                        </div>
                      </div>

                      <div className="bg-bg-panel/30 border border-border/60 rounded p-2.5">
                        <div className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-1.5">Major Shareholders</div>
                        <div className="space-y-1 text-xs font-mono">
                          {p.ownership?.major_shareholders?.map((sh: any, i: number) => (
                            <div key={i} className="flex justify-between text-[11px]">
                              <span className="text-text-secondary truncate max-w-[130px]">{sh.name}</span>
                              <span className="font-bold text-accent">{sh.pct}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 2. Solvency & Risk Tab */}
              {activeTab === 'solvency' && (
                <div className="space-y-4">
                  {/* Solvency stats cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: 'Altman Z-Score', value: r.z_score, note: r.z_score > 2.9 ? 'Safe Zone (>2.9)' : 'Grey/Distressed', color: getZScoreColor(r.z_score) },
                      { label: 'Piotroski F-Score', value: `${r.f_score}/9`, note: r.f_score >= 7 ? 'Strong Efficiency' : 'Leveraged', color: 'text-accent' },
                      { label: 'Merton Distance to Default', value: `${r.distance_to_default} σ`, note: 'Asset units limit default risk', color: 'text-secondary' },
                      { label: 'Probability of Default (1Y)', value: `${r.probability_of_default}%`, note: 'Physical credit likelihood', color: r.probability_of_default > 1.0 ? 'text-negative' : 'text-positive' },
                    ].map((card, i) => (
                      <div key={i} className="bg-bg-panel rounded-lg p-3 border border-border text-center">
                        <div className="text-[10px] text-text-tertiary uppercase">{card.label}</div>
                        <div className={`font-mono text-lg font-black mt-1 ${card.color}`}>{card.value}</div>
                        <div className="text-[9px] text-text-tertiary font-mono mt-0.5">{card.note}</div>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Altman Z-Score explanation */}
                    <div className="panel p-4 space-y-3">
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider">Altman Z-Score Distress Diagnostics</h3>
                      <p className="text-xs text-text-secondary leading-relaxed font-mono">
                        The Altman Z-score utilizes 5 financial ratios representing working capital, retained earnings, profitability, asset turnover, and capital structure leverage to identify standard corporate insolvency.
                      </p>
                      <div className="space-y-2 border-t border-border/40 pt-3 text-xs font-mono">
                        <div className="flex justify-between items-center bg-positive/10 border border-positive/20 rounded px-2.5 py-1.5">
                          <div>
                            <span className="font-bold text-positive">Safe Zone (&gt; 2.90)</span>
                            <p className="text-[9px] text-text-tertiary">Zero near-term distress warning</p>
                          </div>
                          {r.z_score > 2.9 && <CheckCircle2 className="w-5 h-5 text-positive" />}
                        </div>
                        <div className="flex justify-between items-center bg-warning/10 border border-warning/20 rounded px-2.5 py-1.5">
                          <div>
                            <span className="font-bold text-warning">Grey Zone (1.20 - 2.90)</span>
                            <p className="text-[9px] text-text-tertiary">Moderate refinancing caution required</p>
                          </div>
                          {r.z_score <= 2.9 && r.z_score >= 1.2 && <AlertTriangle className="w-5 h-5 text-warning" />}
                        </div>
                        <div className="flex justify-between items-center bg-negative/10 border border-negative/20 rounded px-2.5 py-1.5">
                          <div>
                            <span className="font-bold text-negative">Distressed Zone (&lt; 1.20)</span>
                            <p className="text-[9px] text-text-tertiary">Elevated corporate bankruptcy risk</p>
                          </div>
                          {r.z_score < 1.2 && <AlertTriangle className="w-5 h-5 text-negative" />}
                        </div>
                      </div>
                    </div>

                    {/* Ratings Migration */}
                    <div className="panel p-4 space-y-3">
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider">Ratings Agency Alignment</h3>
                      <p className="text-xs text-text-secondary leading-relaxed font-mono">
                        Moody's, Standard & Poor's, and Fitch maintain high alignment on {p.name}'s creditworthiness. Historically, {p.ticker} has displayed absolute capital structure stability.
                      </p>
                      <table className="w-full text-xs font-mono mt-4">
                        <thead>
                          <tr className="border-b border-border/80">
                            <th className="pb-2 text-left text-[10px] text-text-tertiary uppercase">Rating Agency</th>
                            <th className="pb-2 text-right text-[10px] text-text-tertiary uppercase">Current Rating</th>
                            <th className="pb-2 text-right text-[10px] text-text-tertiary uppercase">Watchlist Status</th>
                            <th className="pb-2 text-right text-[10px] text-text-tertiary uppercase">Credit Outlook</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/30">
                          <tr>
                            <td className="py-2 text-text font-semibold">S&P Global Ratings</td>
                            <td className="py-2 text-right font-bold text-positive">{ra.sp}</td>
                            <td className="py-2 text-right text-text-secondary">NONE</td>
                            <td className="py-2 text-right text-secondary uppercase font-bold">{ra.outlook}</td>
                          </tr>
                          <tr>
                            <td className="py-2 text-text font-semibold">Moody's Investors Service</td>
                            <td className="py-2 text-right font-bold text-accent">{ra.moodys}</td>
                            <td className="py-2 text-right text-text-secondary">NONE</td>
                            <td className="py-2 text-right text-secondary uppercase font-bold">{ra.outlook}</td>
                          </tr>
                          <tr>
                            <td className="py-2 text-text font-semibold">Fitch Ratings</td>
                            <td className="py-2 text-right font-bold text-positive">{ra.fitch}</td>
                            <td className="py-2 text-right text-text-secondary">NONE</td>
                            <td className="py-2 text-right text-secondary uppercase font-bold">{ra.outlook}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* 3. Debt Structure Tab */}
              {activeTab === 'debt' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Left Column: Debt metrics & details */}
                  <div className="panel p-4 space-y-4">
                    <h3 className="text-xs font-bold text-accent uppercase tracking-wider">Debt Concentration Metrics</h3>
                    <div className="space-y-3 text-xs font-mono">
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Total Outstanding Debt</span>
                        <span className="text-text font-bold">${d.total_debt} B</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Short-Term Debt</span>
                        <span className="text-text font-bold">${d.st_debt} B</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Long-Term Debt</span>
                        <span className="text-text font-bold">${d.lt_debt} B</span>
                      </div>
                      <div className="flex justify-between border-t border-border/40 pt-2 font-semibold">
                        <span className="text-accent">Weighted Average Coupon (WAC)</span>
                        <span className="text-text font-black">{d.wac}%</span>
                      </div>
                      <div className="flex justify-between border-b border-border/40 pb-2 font-semibold">
                        <span className="text-secondary">Weighted Average Maturity (WAM)</span>
                        <span className="text-text font-black">{d.wam} Years</span>
                      </div>
                    </div>

                    <div className="bg-bg-panel/30 border border-border/60 rounded p-3 mt-4 space-y-2">
                      <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider">Instrument Categories</h4>
                      <div className="space-y-1.5">
                        {d.types?.map((t: any, i: number) => (
                          <div key={i} className="flex justify-between text-xs font-mono">
                            <span className="text-text-secondary truncate max-w-[170px]">{t.name}</span>
                            <span className="font-bold text-text">{t.pct}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Maturity ladder chart */}
                  <div className="panel md:col-span-2 p-4 flex flex-col justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-2">Debt Refinancing & Maturity Ladder</h3>
                      <p className="text-xs text-text-secondary mb-4 font-mono">
                        Visualizing outstanding maturities year-by-year helps identify cash flow mismatch and systemic funding rollover risks.
                      </p>
                    </div>

                    <div className="h-60 mt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={maturityChartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                          <XAxis dataKey="name" tick={{ fill: '#888', fontSize: 10 }} axisLine={{ stroke: '#222' }} />
                          <YAxis tick={{ fill: '#888', fontSize: 10 }} axisLine={{ stroke: '#222' }} unit="B" />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#0B0B0B', border: '1px solid #333', fontSize: 11 }}
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                          />
                          <Bar dataKey="Maturity" fill="#D97706" radius={[4, 4, 0, 0]}>
                            {maturityChartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#10B981' : '#F59E0B'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              {/* 4. Financials & Peer Comparison Tab */}
              {activeTab === 'ratios' && (
                <div className="space-y-4">
                  {/* Historical Financials Table */}
                  <div className="panel p-4">
                    <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-2">5-Year Historical Performance Data</h3>
                    <div className="overflow-x-auto mt-3">
                      <table className="w-full text-xs font-mono">
                        <thead>
                          <tr className="border-b border-border/80 text-text-tertiary">
                            <th className="pb-2 text-left">FINANCIAL ITEM</th>
                            {history5y.years?.map((y: number) => (
                              <th key={y} className="pb-2 text-right font-bold">{y}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/20 text-text-secondary">
                          <tr>
                            <td className="py-2 text-text font-bold">Total Revenue ($B)</td>
                            {history5y.revenue?.map((v: number, i: number) => (
                              <td key={i} className="py-2 text-right font-bold text-text">{v.toFixed(1)}</td>
                            ))}
                          </tr>
                          <tr>
                            <td className="py-2 text-text">EBITDA ($B)</td>
                            {history5y.ebitda?.map((v: number, i: number) => (
                              <td key={i} className="py-2 text-right">{v.toFixed(1)}</td>
                            ))}
                          </tr>
                          <tr>
                            <td className="py-2 text-text">Gross Margin (%)</td>
                            {history5y.gross_margin?.map((v: number, i: number) => (
                              <td key={i} className="py-2 text-right text-positive font-semibold">{v}%</td>
                            ))}
                          </tr>
                          <tr>
                            <td className="py-2 text-text">Cash Reserves ($B)</td>
                            {history5y.cash?.map((v: number, i: number) => (
                              <td key={i} className="py-2 text-right text-accent font-bold">{v.toFixed(1)}</td>
                            ))}
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Competitor Matrix */}
                  <div className="panel p-4">
                    <h3 className="text-xs font-bold text-accent uppercase tracking-wider mb-2">Peer Competitive Leverage Matrix</h3>
                    <div className="overflow-x-auto mt-3">
                      <table className="w-full text-xs font-mono">
                        <thead>
                          <tr className="border-b border-border/80 text-text-tertiary">
                            <th className="pb-2 text-left">PEER COMPETITOR</th>
                            <th className="pb-2 text-center">RATING</th>
                            <th className="pb-2 text-right">DEBT / EBITDA</th>
                            <th className="pb-2 text-right">INTEREST COVERAGE</th>
                            <th className="pb-2 text-right">NET MARGIN</th>
                            <th className="pb-2 text-right">ALTMAN Z-SCORE</th>
                            <th className="pb-2 text-right">MERTON DISTANCE</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/20 text-text-secondary">
                          {peers.map((peer: any, idx: number) => (
                            <tr key={idx} className={peer.ticker === p.ticker ? 'bg-accent/5 font-semibold text-text' : ''}>
                              <td className="py-2.5 flex items-center gap-1.5">
                                <span>{peer.name}</span>
                                <span className="text-[10px] text-text-tertiary uppercase">({peer.ticker})</span>
                              </td>
                              <td className="py-2.5 text-center text-positive font-bold">{peer.rating}</td>
                              <td className="py-2.5 text-right">{peer.debt_to_ebitda}x</td>
                              <td className="py-2.5 text-right text-accent">{peer.interest_coverage}x</td>
                              <td className="py-2.5 text-right text-positive">{peer.net_margin}%</td>
                              <td className="py-2.5 text-right">{peer.z_score}</td>
                              <td className="py-2.5 text-right">{peer.distance_to_default} σ</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* 5. Macro Stress calculator Tab */}
              {activeTab === 'scenarios' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Left Column: Stress parameters */}
                  <div className="panel p-4 space-y-4">
                    <h3 className="text-xs font-bold text-accent uppercase tracking-wider">Macro Stress Selectors</h3>
                    <p className="text-xs text-text-secondary leading-relaxed font-mono">
                      Simulate extreme yield transitions and parallel interest rate movements to calculate physical changes in defaults and bond pricing.
                    </p>
                    <div className="space-y-2 mt-4">
                      {[
                        { id: 'recession', label: 'Severe Recession' },
                        { id: 'parallel_up_100', label: 'Fed +1.0% Rate Hike' },
                        { id: 'parallel_down_100', label: 'Fed -1.0% Rate Cut' },
                        { id: 'downgrade', label: 'Downgrade shock' },
                      ].map((scen) => (
                        <button
                          key={scen.id}
                          onClick={() => setSelectedScenario(scen.id)}
                          className={`w-full text-left px-3 py-2 rounded text-xs font-semibold font-mono border transition-all ${selectedScenario === scen.id
                              ? 'bg-accent/15 border-accent/40 text-accent font-black'
                              : 'hover:bg-bg-hover text-text-secondary border-transparent'
                            }`}
                        >
                          {scen.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Right Column: Calculated scenario impact */}
                  <div className="panel md:col-span-2 p-4 space-y-4">
                    <div className="border-b border-border/60 pb-2">
                      <span className="text-[10px] uppercase text-text-tertiary">Selected stress profile</span>
                      <h3 className="text-sm font-bold text-text uppercase font-mono mt-0.5">{activeScenario.label}</h3>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-bg-panel/40 border border-border/80 rounded p-3">
                        <span className="text-[10px] text-text-tertiary uppercase">Stress Probability of Default</span>
                        <div className="font-mono text-lg font-black text-negative mt-1">{activeScenario.default_prob_new}%</div>
                        <p className="text-[9px] text-text-tertiary font-mono mt-0.5">
                          Base: {r.probability_of_default}% (Δ +{(activeScenario.default_prob_new - r.probability_of_default).toFixed(4)}%)
                        </p>
                      </div>

                      <div className="bg-bg-panel/40 border border-border/80 rounded p-3">
                        <span className="text-[10px] text-text-tertiary uppercase">Credit Spread Shift</span>
                        <div className="font-mono text-lg font-black text-accent mt-1">
                          {activeScenario.spread_impact_bps > 0 ? '+' : ''}
                          {activeScenario.spread_impact_bps} bps
                        </div>
                        <p className="text-[9px] text-text-tertiary font-mono mt-0.5">
                          Adjusts target spreads to {((m.yield_spread_pct * 100) + activeScenario.spread_impact_bps).toFixed(0)} bps
                        </p>
                      </div>
                    </div>

                    <div className="bg-negative/5 border border-negative/30 rounded p-4.5 space-y-2 mt-4">
                      <h4 className="text-xs font-bold text-negative uppercase tracking-wider flex items-center gap-1.5 font-mono">
                        <AlertTriangle className="w-4.5 h-4.5" /> Credit Sensitivity Analysis
                      </h4>
                      <p className="text-xs text-text-secondary leading-relaxed font-mono">
                        Under this scenario, a portfolio hold-to-maturity position is estimated to experience a capital price change of <span className="font-black text-negative font-mono">{activeScenario.price_impact_pct}%</span> due to duration sensitivity and yield curve shifts.
                      </p>
                      <div className="text-xs font-mono font-semibold text-text-secondary mt-2 flex justify-between">
                        <span>ESTIMATED PRICE DRAWDOWN:</span>
                        <span className="text-negative font-bold">{activeScenario.price_impact_pct}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 6. AI Credit committee Memo Tab */}
              {activeTab === 'memo' && (
                <div className="panel p-4 space-y-4">
                  <div className="flex items-center justify-between border-b border-border/60 pb-3">
                    <div>
                      <h3 className="text-xs font-bold text-accent uppercase tracking-wider">Institutional AI Credit Committee Briefing</h3>
                      <p className="text-xs text-text-secondary font-mono mt-0.5">
                        Compile a professional 16-section corporate credit memorandum detailing leverage, solvency, and investment stances.
                      </p>
                    </div>

                    {!memo && (
                      <button
                        onClick={generateMemo}
                        disabled={memoLoading}
                        className="bg-accent hover:bg-accent-hover text-bg-panel px-4 py-1.5 rounded font-mono font-bold text-xs flex items-center gap-1.5 transition-all disabled:opacity-50"
                      >
                        <FileText className="w-4 h-4" />
                        <span>{memoLoading ? 'COMPILING MEMORANDUM...' : 'GENERATE CREDIT MEMO'}</span>
                      </button>
                    )}
                  </div>

                  {memoLoading ? (
                    <div className="py-20 text-center space-y-3">
                      <div className="w-8 h-8 border-3 border-accent border-t-transparent rounded-full animate-spin mx-auto" />
                      <p className="text-xs text-text-tertiary font-mono">PARSING BALANCE SHEETS & RUNNING SOLVENCY ENGINE FOR COMMITTEE BRIEF...</p>
                    </div>
                  ) : memo ? (
                    <div className="space-y-4">
                      {/* Memo controls */}
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => window.print()}
                          className="bg-bg-panel border border-border hover:bg-bg-hover text-text px-3 py-1 rounded text-xs font-mono font-semibold transition-all"
                        >
                          PRINT MEMO
                        </button>
                        <button
                          onClick={() => setMemo('')}
                          className="bg-bg-panel border border-border hover:bg-bg-hover text-text-tertiary px-3 py-1 rounded text-xs font-mono font-semibold transition-all"
                        >
                          CLEAR MEMO
                        </button>
                      </div>

                      {/* Renders beautifully styled credit memo */}
                      <div className="bg-[#080808] border border-border/80 rounded-lg p-6 max-h-[60vh] overflow-y-auto font-mono text-xs text-text-secondary leading-relaxed whitespace-pre-wrap select-text scrollbar-hide">
                        {memo}
                      </div>
                    </div>
                  ) : (
                    <div className="py-16 text-center text-text-tertiary font-mono text-xs">
                      Click the button above to generate a complete institutional solvency research memo (replaces 300 pages of filings).
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
