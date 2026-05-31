/**
 * Centralized API Configuration & HTTP Client
 * 
 * Provides unified API endpoint management and HTTP utilities
 * for all frontend services.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export const API_ENDPOINTS = {
  // Dashboard
  DASHBOARD: `${API_URL}/api/v1/dashboard`,
  
  // Treasury
  TREASURY: {
    YIELD_CURVE: `${API_URL}/api/v1/treasury/yield-curve`,
    AUCTIONS: `${API_URL}/api/v1/treasury/auctions`,
    RATES_TABLE: `${API_URL}/api/v1/treasury/rates-table`,
  },
  
  // Market Data
  MARKET: {
    SUMMARY: `${API_URL}/api/v1/market/summary`,
    HEATMAP: `${API_URL}/api/v1/market/heatmap`,
    TOP_MOVERS: `${API_URL}/api/v1/market/top-movers`,
  },
  
  // Credit Analysis
  CREDIT: {
    SPREADS: `${API_URL}/api/v1/credit/spreads`,
    RATINGS: `${API_URL}/api/v1/credit/ratings`,
  },
  
  // Portfolio
  PORTFOLIO: {
    LIST: `${API_URL}/api/v1/portfolio`,
    CREATE: `${API_URL}/api/v1/portfolio`,
    ANALYTICS: `${API_URL}/api/v1/portfolio/analytics`,
  },
  
  // Watchlist
  WATCHLIST: {
    LIST: `${API_URL}/api/v1/watchlist`,
    ADD: `${API_URL}/api/v1/watchlist`,
    REMOVE: `${API_URL}/api/v1/watchlist`,
  },
  
  // Alerts
  ALERTS: {
    LIST: `${API_URL}/api/v1/alerts`,
    CREATE: `${API_URL}/api/v1/alerts`,
    UPDATE: `${API_URL}/api/v1/alerts`,
  },
  
  // Analytics
  ANALYTICS: {
    COMPARISON: `${API_URL}/api/v1/analytics/comparison`,
    SCENARIO: `${API_URL}/api/v1/analytics/scenario`,
    RISK: `${API_URL}/api/v1/analytics/risk`,
  },
  
  // AI Services
  AI: {
    CHAT: `${API_URL}/api/v1/ai/chat`,
    INSIGHTS: `${API_URL}/api/v1/ai/insights`,
  },
  
  // News
  NEWS: {
    LATEST: `${API_URL}/api/v1/news`,
    SEARCH: `${API_URL}/api/v1/news/search`,
  },
  
  // Authentication
  AUTH: {
    LOGIN: `${API_URL}/api/v1/auth/login`,
    REGISTER: `${API_URL}/api/v1/auth/register`,
    LOGOUT: `${API_URL}/api/v1/auth/logout`,
  },
  
  // Macro Indicators
  MACRO: {
    INDICATORS: `${API_URL}/api/v1/macro/indicators`,
    CPI: `${API_URL}/api/v1/macro/cpi`,
    GDP: `${API_URL}/api/v1/macro/gdp`,
  },
} as const;

/**
 * Fetch wrapper with error handling and response typing
 */
export async function fetchAPI<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(typeof options.headers === 'object' && options.headers !== null 
      ? Object.fromEntries(Object.entries(options.headers)) 
      : {}),
  };

  // Add auth token if available
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(endpoint, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Fetch failed for ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Get API base URL
 */
export function getAPIUrl(): string {
  return API_URL;
}

/**
 * Get WebSocket URL for real-time updates
 */
export function getWebSocketUrl(): string {
  return API_URL.replace('http', 'ws');
}
