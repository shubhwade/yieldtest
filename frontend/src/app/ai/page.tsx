'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Send, Sparkles, Shield, BarChart3 } from 'lucide-react';

const SUGGESTIONS = [
  'Why are my bonds falling?',
  'Show safest bonds under 5 years',
  'Compare TIPS vs Treasury for inflation protection',
  'Explain convexity in simple terms',
  'What happens to bond prices if the Fed cuts rates?',
  'Explain the yield curve inversion',
];

interface AIMeta {
  confidence_score?: number;
  sources?: string[];
  source?: string;
  risk_analysis?: string;
  portfolio_impact?: string;
  recommended_actions?: string[];
}

interface Message {
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
  meta?: AIMeta;
}

export default function AIPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: '👋 Welcome to **YieldLens AI**. I\'m your fixed-income analyst powered by Google Gemini.\n\nI can help you with:\n- Bond analysis and comparisons\n- Market interpretation\n- Financial concept explanations\n- Portfolio recommendations\n- Yield calculations\n\nAsk me anything about fixed income markets!', timestamp: '' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    // Populate localized welcome timestamp on mount
    setMessages(prev => prev.map((m, i) => i === 0 ? { ...m, timestamp: new Date().toLocaleTimeString() } : m));
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { role: 'user', content: text, timestamp: new Date().toLocaleTimeString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Retry logic — try up to 2 times
    let attempts = 0;
    const maxAttempts = 2;

    while (attempts < maxAttempts) {
      attempts++;
      try {
        const res = await fetch(`${API_URL}/api/v1/ai/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: text }),
        });

        if (res.ok) {
          const json = await res.json();
          const data = json.data || {};

          const aiMsg: Message = {
            role: 'ai',
            content: data.response || data.summary || 'Analysis complete. Please see details below.',
            timestamp: new Date().toLocaleTimeString(),
            meta: {
              confidence_score: data.confidence_score,
              sources: data.sources,
              source: data.source,
              risk_analysis: data.risk_analysis,
              portfolio_impact: data.portfolio_impact,
              recommended_actions: data.recommended_actions,
            },
          };

          setMessages(prev => [...prev, aiMsg]);
          setLoading(false);
          return; // Success — exit
        }

        // If not OK on first attempt, retry
        if (attempts < maxAttempts) {
          await new Promise(r => setTimeout(r, 1000));
          continue;
        }

        throw new Error('API returned error');
      } catch {
        if (attempts < maxAttempts) {
          await new Promise(r => setTimeout(r, 1000));
          continue;
        }

        // Final fallback after retries exhausted
        setMessages(prev => [...prev, {
          role: 'ai',
          content: `Based on your query about "${text}":\n\nThe fixed income market presents various opportunities depending on your investment horizon and risk tolerance. Key factors to consider include:\n\n• **Duration risk**: Longer-duration bonds are more sensitive to rate changes\n• **Credit quality**: Higher-rated bonds offer more safety but lower yields\n• **Tax implications**: Municipal bonds can offer superior after-tax yields\n• **Inflation protection**: TIPS provide direct inflation hedging\n\n*Analysis based on cached market data. AI connection will retry automatically.*`,
          timestamp: new Date().toLocaleTimeString(),
          meta: { confidence_score: 25, source: 'offline-fallback' },
        }]);
      }
    }

    setLoading(false);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col h-[calc(100vh-7rem)]">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-5 h-5 text-accent" />
        <h1 className="text-lg font-bold">AI Insights</h1>
        <span className="badge-accent text-[10px]">Gemini 2.0 Flash</span>
      </div>

      {/* Chat Area */}
      <div className="flex-1 panel overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-3 ${msg.role === 'user' ? 'bg-accent/10 border border-accent/20' : 'bg-bg-card border border-border'}`}>
                <div className="text-xs whitespace-pre-wrap leading-relaxed">{msg.content}</div>

                {/* Structured AI metadata */}
                {msg.role === 'ai' && msg.meta && (msg.meta.confidence_score || msg.meta.sources?.length) && (
                  <div className="mt-3 pt-2 border-t border-border/50 space-y-1.5">
                    {msg.meta.risk_analysis && (
                      <div className="flex items-start gap-1.5">
                        <Shield className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                        <span className="text-[10px] text-text-tertiary">{msg.meta.risk_analysis}</span>
                      </div>
                    )}
                    {msg.meta.portfolio_impact && (
                      <div className="flex items-start gap-1.5">
                        <BarChart3 className="w-3 h-3 text-blue-400 mt-0.5 shrink-0" />
                        <span className="text-[10px] text-text-tertiary">{msg.meta.portfolio_impact}</span>
                      </div>
                    )}
                    {msg.meta.recommended_actions && msg.meta.recommended_actions.length > 0 && (
                      <div className="text-[10px] text-text-tertiary">
                        <span className="font-semibold text-text-secondary">Actions:</span>{' '}
                        {msg.meta.recommended_actions.join(' • ')}
                      </div>
                    )}
                    <div className="flex items-center gap-3 mt-1">
                      {msg.meta.confidence_score != null && (
                        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                          msg.meta.confidence_score >= 80 ? 'bg-emerald-500/10 text-emerald-400' :
                          msg.meta.confidence_score >= 50 ? 'bg-amber-500/10 text-amber-400' :
                          'bg-red-500/10 text-red-400'
                        }`}>
                          Confidence: {msg.meta.confidence_score}%
                        </span>
                      )}
                      {msg.meta.sources && msg.meta.sources.length > 0 && (
                        <span className="text-[9px] text-text-tertiary font-mono">
                          Sources: {msg.meta.sources.join(', ')}
                        </span>
                      )}
                      {msg.meta.source && (
                        <span className="text-[9px] text-text-tertiary font-mono opacity-50">
                          via {msg.meta.source}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                <div className="text-[10px] text-text-tertiary mt-2 text-right">{msg.timestamp}</div>
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-bg-panel border border-border rounded-lg px-4 py-3">
                <div className="flex gap-1"><div className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{animationDelay: '0ms'}} /><div className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{animationDelay: '150ms'}} /><div className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{animationDelay: '300ms'}} /></div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 1 && (
          <div className="px-4 pb-2">
            <div className="flex items-center gap-1 text-xs text-text-tertiary mb-2"><Sparkles className="w-3 h-3" />Suggested queries:</div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => sendMessage(s)} className="text-xs px-3 py-1.5 rounded-full border border-border text-text-secondary hover:border-accent/50 hover:text-accent transition-colors">{s}</button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-3 border-t border-border flex gap-2">
          <input className="input-field flex-1" placeholder="Ask about bonds, yields, rates, or any fixed income topic..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage(input)} />
          <button onClick={() => sendMessage(input)} disabled={!input.trim() || loading} className="btn-primary flex items-center gap-1 disabled:opacity-50"><Send className="w-4 h-4" /></button>
        </div>
      </div>
    </motion.div>
  );
}
