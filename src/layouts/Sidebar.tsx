'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, TrendingUp, Search, GitCompare, Calculator,
  Activity, Shield, Building2, Briefcase, Eye, Bell, Globe,
  Brain, Newspaper, Settings, ChevronLeft, ChevronRight, Zap,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/markets', label: 'Markets', icon: TrendingUp },
  { href: '/screener', label: 'Bond Screener', icon: Search },
  { href: '/comparison', label: 'FI Comparison', icon: GitCompare },
  { href: '/analytics', label: 'Yield Analytics', icon: Calculator },
  { href: '/treasury', label: 'Treasury Curve', icon: Activity },
  { href: '/credit', label: 'Credit Analysis', icon: Shield },
  { href: '/muni', label: 'Muni Intelligence', icon: Building2 },
  { href: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { href: '/watchlist', label: 'Watchlist', icon: Eye },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/macro', label: 'Macro Dashboard', icon: Globe },
  { href: '/ai', label: 'AI Insights', icon: Brain },
  { href: '/news', label: 'News', icon: Newspaper },
  { href: '/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="h-screen bg-[#0A0A0A] border-r border-border flex flex-col shrink-0 relative z-50"
    >
      {/* Logo Area */}
      <Link href="/dashboard" className="h-20 flex flex-col justify-center px-6 border-b border-border gap-1 group cursor-pointer overflow-hidden relative">
        <div className="flex flex-col transition-transform duration-300 group-hover:scale-[1.01]">
          {!collapsed ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col"
            >
              <span className="text-2xl font-bold tracking-tighter flex items-baseline leading-none mb-1">
                <span className="text-text">Yield</span>
                <span className="text-accent">Lens</span>
              </span>
              <span className="text-[10px] text-text-secondary font-medium uppercase tracking-[0.2em] leading-none opacity-80">
                The Bloomberg for Bond Investors
              </span>
            </motion.div>
          ) : (
            <div className="flex items-center justify-center">
              <span className="text-xl font-black text-accent tracking-tighter">YL</span>
            </div>
          )}
        </div>
        <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
      </Link>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 scrollbar-hide">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href}>
              <div
                className={`group flex items-center gap-3 mx-3 px-3 py-2.5 rounded-md text-sm transition-all duration-200 relative ${
                  isActive
                    ? 'bg-accent/10 text-accent font-semibold shadow-sm shadow-accent/5'
                    : 'text-text-secondary hover:text-text hover:bg-bg-hover'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute left-0 top-2 bottom-2 w-[3px] bg-accent rounded-r-full"
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}
                <Icon className={`w-5 h-5 shrink-0 transition-colors duration-200 ${isActive ? 'text-accent' : 'text-text-secondary group-hover:text-text'}`} />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="truncate"
                  >
                    {item.label}
                  </motion.span>
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className="h-10 flex items-center justify-center border-t border-border text-text-secondary hover:text-text hover:bg-bg-hover transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </motion.aside>
  );
}
