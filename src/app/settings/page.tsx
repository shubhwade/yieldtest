'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, 
  User, 
  Palette, 
  SlidersHorizontal, 
  Bell, 
  Info, 
  Zap, 
  Globe, 
  Lock, 
  LogOut,
  Accessibility
} from 'lucide-react';

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4 max-w-4xl">
      <h1 className="text-lg font-bold">Settings</h1>

      {/* Profile Settings */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold">Account Profile</span>
          </div>
        </div>
        <div className="p-4 grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-text-secondary mb-1 block">Full Name</label>
            <input className="input-field w-full" type="text" defaultValue="Institutional Investor" />
          </div>
          <div>
            <label className="text-xs text-text-secondary mb-1 block">Email Address</label>
            <input className="input-field w-full" type="email" defaultValue="investor@yieldlens.com" />
          </div>
        </div>
      </div>

      {/* Appearance */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Palette className="w-4 h-4 text-secondary" />
            <span className="text-sm font-semibold">Appearance</span>
          </div>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { label: 'Bloomberg (Dark)', active: true },
              { label: 'Terminal (OLED)', active: false },
              { label: 'Financial (Slate)', active: false },
            ].map((theme, i) => (
              <button key={i} className={`px-4 py-3 rounded-lg border text-xs transition-colors text-left flex items-center justify-between ${theme.active ? 'border-accent bg-accent/5 text-accent font-bold' : 'border-border text-text-secondary hover:border-accent/30'}`}>
                {theme.label}
                {theme.active && <div className="w-2 h-2 rounded-full bg-accent" />}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Dashboard Preferences */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-blueAccent" />
            <span className="text-sm font-semibold">Dashboard & Screener</span>
          </div>
        </div>
        <div className="p-4 grid grid-cols-2 gap-4">
          <div><label className="text-xs text-text-secondary mb-1 block">Default Currency</label><select className="input-field w-full"><option>USD (United States Dollar)</option><option>EUR (Euro)</option><option>GBP (British Pound)</option></select></div>
          <div><label className="text-xs text-text-secondary mb-1 block">Language</label><select className="input-field w-full"><option>English (US)</option><option>English (UK)</option><option>German</option><option>French</option></select></div>
          <div><label className="text-xs text-text-secondary mb-1 block">Screener Page Size</label><select className="input-field w-full"><option>25 rows</option><option>50 rows</option><option>100 rows</option></select></div>
          <div><label className="text-xs text-text-secondary mb-1 block">Tax Bracket Assumption</label><select className="input-field w-full"><option>32% (Standard)</option><option>24%</option><option>35%</option><option>37%</option></select></div>
        </div>
      </div>

      {/* Notifications */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold">Notifications</span>
          </div>
        </div>
        <div className="p-4 space-y-3">
          {['Yield change alerts', 'Curve inversion warnings', 'Credit rating changes', 'Daily market brief', 'Macro event notifications'].map((pref, i) => (
            <label key={i} className="flex items-center justify-between cursor-pointer group">
              <span className="text-xs text-text-secondary group-hover:text-text transition-colors">{pref}</span>
              <input type="checkbox" defaultChecked={i < 3} className="w-4 h-4 rounded bg-bg-panel border-border accent-accent" />
            </label>
          ))}
        </div>
      </div>

      {/* Privacy & Accessibility */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-text-secondary" />
              <span className="text-sm font-semibold">Privacy</span>
            </div>
          </div>
          <div className="p-4">
            <button className="text-xs text-text-secondary hover:text-accent transition-colors underline">Configure Privacy Settings</button>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <Accessibility className="w-4 h-4 text-text-secondary" />
              <span className="text-sm font-semibold">Accessibility</span>
            </div>
          </div>
          <div className="p-4">
            <button className="text-xs text-text-secondary hover:text-accent transition-colors underline">Enable Screen Reader Optimization</button>
          </div>
        </div>
      </div>

      {/* Logout & Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <button onClick={handleSave} className="btn-primary">
          {saved ? '✅ Configuration Saved' : 'Save Changes'}
        </button>
        <button className="flex items-center gap-2 px-4 py-2 text-negative hover:bg-negative/10 rounded-md transition-colors text-sm font-semibold">
          <LogOut className="w-4 h-4" />
          Logout from Terminal
        </button>
      </div>

      {/* About */}
      <div className="panel opacity-60">
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center"><Zap className="w-5 h-5 text-accent" /></div>
            <div>
              <div className="text-xs font-bold">YIELDLENS <span className="text-text-tertiary font-normal">v1.0.0</span></div>
              <div className="text-[10px] text-text-tertiary">Institutional Fixed-Income Intelligence</div>
            </div>
          </div>
          <div className="text-[10px] text-text-tertiary text-right">
            © 2026 YieldLens — Bloomberg-grade analytics
          </div>
        </div>
      </div>
    </motion.div>
  );
}
