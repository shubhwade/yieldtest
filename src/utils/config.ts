/**
 * Environment configuration
 * Centralizes all configuration values
 */

export const CONFIG = {
  // API (Using relative path for Vercel Serverless)
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  
  // WebSocket (Note: Persistent WebSockets are not supported on Vercel Serverless)
  WS_URL: '',
  
  // App metadata
  APP_NAME: 'YieldLens',
  APP_VERSION: '1.0.0',
  
  // Feature flags
  FEATURES: {
    AI_CHAT: true,
    PORTFOLIO_ANALYTICS: true,
    RISK_ANALYSIS: true,
    SCENARIO_TESTING: true,
  },
  
  // UI
  UI: {
    ANIMATION_DURATION: 300,
    TOAST_DURATION: 4000,
    DEBOUNCE_DELAY: 300,
  },
  
  // Data refresh intervals (ms)
  REFRESH_INTERVALS: {
    DASHBOARD: 30000,      // 30 seconds
    MARKET_DATA: 60000,    // 1 minute
    NEWS: 120000,          // 2 minutes
    ALERTS: 10000,         // 10 seconds
  },
  
  // Limits
  LIMITS: {
    MAX_PORTFOLIO_SIZE: 1000,
    MAX_WATCHLIST_SIZE: 100,
    MAX_ALERTS: 50,
    API_TIMEOUT: 30000,
  },
} as const;

export type Config = typeof CONFIG;
