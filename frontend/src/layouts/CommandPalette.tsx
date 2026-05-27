'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, FileText, Briefcase, Eye, Globe, Sparkles, X, CornerDownLeft, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any>({ bonds: [], news: [], portfolios: [], watchlists: [], macro: [] });
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
      const recents = localStorage.getItem('yl_recent_searches');
      if (recents) {
        setRecentSearches(JSON.parse(recents));
      } else {
        setRecentSearches(['10Y Treasury', 'Apple', 'Inflation CPI', 'High Yield']);
      }
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Handle Search API
  useEffect(() => {
    if (!query) {
      setResults({ bonds: [], news: [], portfolios: [], watchlists: [], macro: [] });
      setSuggestions(['10Y Treasury Yield', 'US Corporate High Yield', 'Inflation Rate (CPI)', 'Risk Parity strategy']);
      return;
    }

    const delayDebounce = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/v1/search/global`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });
        if (res.ok) {
          const json = await res.json();
          if (json.success) {
            setResults(json.results);
            if (json.suggestions) setSuggestions(json.suggestions);
          }
        }
      } catch (e) {
        console.error('Global search error:', e);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(delayDebounce);
  }, [query, API_URL]);

  const selectSearch = (q: string) => {
    setQuery(q);
    // Add to recent searches
    const updated = [q, ...recentSearches.filter((item) => item !== q)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('yl_recent_searches', JSON.stringify(updated));
  };

  const clearRecent = (e: React.MouseEvent, q: string) => {
    e.stopPropagation();
    const updated = recentSearches.filter((item) => item !== q);
    setRecentSearches(updated);
    localStorage.setItem('yl_recent_searches', JSON.stringify(updated));
  };

  // Keyboard navigation through search categories
  const allFlattenedItems = [
    ...results.macro.map((m: any) => ({ ...m, category: 'Macro', icon: Globe })),
    ...results.portfolios.map((p: any) => ({ ...p, category: 'Portfolio', icon: Briefcase })),
    ...results.watchlists.map((w: any) => ({ ...w, category: 'Watchlist', icon: Eye })),
    ...results.bonds.map((b: any) => ({ ...b, category: 'Bond', icon: Sparkles })),
    ...results.news.map((n: any) => ({ ...n, category: 'News', icon: FileText })),
  ];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, allFlattenedItems.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + allFlattenedItems.length) % Math.max(1, allFlattenedItems.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (allFlattenedItems[selectedIndex]) {
        const item = allFlattenedItems[selectedIndex];
        // Route to the appropriate page
        if (item.category === 'Bond') {
          window.location.href = `/screener?search=${encodeURIComponent(item.cusip || item.name)}`;
        } else if (item.category === 'Portfolio') {
          window.location.href = `/portfolio`;
        } else if (item.category === 'Watchlist') {
          window.location.href = `/watchlist`;
        } else if (item.category === 'Macro') {
          window.location.href = `/macro`;
        } else if (item.category === 'News') {
          if (item.url) window.open(item.url, '_blank');
        }
        onClose();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[10vh] px-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/85 backdrop-blur-sm"
        />

        {/* Command Box */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97, y: -8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.97, y: -8 }}
          transition={{ duration: 0.15, ease: 'easeOut' }}
          className="relative w-full max-w-2xl bg-[#0F0F0F] border border-border/80 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[75vh]"
          onKeyDown={handleKeyDown}
        >
          {/* Search Header */}
          <div className="flex items-center px-4 py-3.5 border-b border-border/60 gap-3">
            <Search className="w-5 h-5 text-text-secondary shrink-0" />
            <input
              ref={inputRef}
              type="text"
              className="w-full bg-transparent border-0 text-sm focus:outline-none placeholder-text-tertiary text-text"
              placeholder="Search by Bond, CUSIP, Issuer, Portfolio, Macro factor, or News... (e.g. AAPL, 10Y)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {loading ? (
              <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin shrink-0" />
            ) : query ? (
              <button onClick={() => setQuery('')}>
                <X className="w-4 h-4 text-text-tertiary hover:text-text shrink-0" />
              </button>
            ) : (
              <span className="text-[10px] bg-bg-panel border border-border px-1.5 py-0.5 rounded text-text-tertiary font-mono select-none">
                ESC
              </span>
            )}
          </div>

          {/* Search Body */}
          <div className="flex-1 overflow-y-auto p-2 min-h-[250px] scrollbar-hide">
            {query === '' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3">
                {/* Recent Searches */}
                <div>
                  <h3 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" /> Recent Terminal Searches
                  </h3>
                  <div className="space-y-1">
                    {recentSearches.map((item, idx) => (
                      <div
                        key={idx}
                        onClick={() => selectSearch(item)}
                        className="group flex items-center justify-between px-2.5 py-2 rounded-md hover:bg-bg-hover cursor-pointer text-xs transition-colors"
                      >
                        <span className="text-text-secondary group-hover:text-text font-medium">{item}</span>
                        <button
                          onClick={(e) => clearRecent(e, item)}
                          className="opacity-0 group-hover:opacity-100 text-text-tertiary hover:text-accent p-0.5"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Autocomplete Suggestions */}
                <div>
                  <h3 className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-accent" /> Autocomplete Suggestions
                  </h3>
                  <div className="space-y-1">
                    {suggestions.map((item, idx) => (
                      <div
                        key={idx}
                        onClick={() => selectSearch(item)}
                        className="flex items-center gap-2 px-2.5 py-2 rounded-md hover:bg-bg-hover cursor-pointer text-xs text-text-secondary hover:text-text transition-colors"
                      >
                        <Search className="w-3.5 h-3.5 text-text-tertiary" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : allFlattenedItems.length === 0 ? (
              <div className="p-8 text-center text-text-tertiary text-xs">
                No matching financial assets or instruments found for "{query}".
              </div>
            ) : (
              <div className="space-y-3 p-1">
                {/* Flattened items with custom categories */}
                {['Macro', 'Portfolio', 'Watchlist', 'Bond', 'News'].map((catName) => {
                  const items = allFlattenedItems.filter((i) => i.category === catName);
                  if (items.length === 0) return null;

                  return (
                    <div key={catName}>
                      <h4 className="text-[9px] font-bold text-text-tertiary uppercase tracking-widest px-2.5 mb-1.5">
                        {catName} Instruments
                      </h4>
                      <div className="space-y-0.5">
                        {items.map((item, idx) => {
                          const flatIdx = allFlattenedItems.findIndex((fi) => fi === item);
                          const isSelected = flatIdx === selectedIndex;
                          const Icon = item.icon;

                          return (
                            <div
                              key={idx}
                              onClick={() => {
                                setSelectedIndex(flatIdx);
                                // Trigger selection
                                if (item.category === 'Bond') {
                                  window.location.href = `/screener?search=${encodeURIComponent(item.cusip || item.name)}`;
                                } else if (item.category === 'Portfolio') {
                                  window.location.href = `/portfolio`;
                                } else if (item.category === 'Watchlist') {
                                  window.location.href = `/watchlist`;
                                } else if (item.category === 'Macro') {
                                  window.location.href = `/macro`;
                                } else if (item.category === 'News') {
                                  if (item.url) window.open(item.url, '_blank');
                                }
                                onClose();
                              }}
                              onMouseEnter={() => setSelectedIndex(flatIdx)}
                              className={`flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors ${
                                isSelected ? 'bg-accent/10 border-l-[3px] border-accent pl-2.5' : 'hover:bg-bg-hover'
                              }`}
                            >
                              <div className="flex items-center gap-3 min-w-0">
                                <Icon className={`w-4 h-4 shrink-0 ${isSelected ? 'text-accent' : 'text-text-tertiary'}`} />
                                <div className="min-w-0">
                                  <div className={`text-xs font-semibold truncate ${isSelected ? 'text-text' : 'text-text-secondary'}`}>
                                    {item.name || item.title || item.issuer}
                                  </div>
                                  <div className="text-[10px] text-text-tertiary flex items-center gap-1.5">
                                    {item.cusip && <span className="font-mono">{item.cusip}</span>}
                                    {item.type && <span className="uppercase">{item.type}</span>}
                                    {item.coupon_rate !== undefined && (
                                      <span>CPN: {item.coupon_rate}%</span>
                                    )}
                                    {item.source && <span>{item.source}</span>}
                                  </div>
                                </div>
                              </div>

                              {isSelected && (
                                <div className="flex items-center gap-1 text-[9px] text-accent font-mono shrink-0 select-none">
                                  <span>SELECT</span>
                                  <CornerDownLeft className="w-2.5 h-2.5" />
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Search Footer */}
          <div className="px-4 py-2 border-t border-border/60 bg-bg-panel/40 flex items-center justify-between text-[9px] text-text-tertiary font-mono select-none">
            <div className="flex items-center gap-3">
              <span>↑↓ Navigation</span>
              <span>↵ Select</span>
              <span>ESC Close</span>
            </div>
            <div className="flex items-center gap-1 text-accent">
              <Sparkles className="w-3 h-3" />
              <span>YIELDLENS FUZZY INTELLIGENCE ACTIVE</span>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
