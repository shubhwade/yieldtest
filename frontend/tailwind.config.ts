import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: '#000000', panel: '#0D1117', card: '#000000', hover: '#1C2333' },
        border: { DEFAULT: '#30363D', light: '#484F58' },
        accent: { DEFAULT: '#2563EB', hover: '#3B82F6', dim: '#2563EB33' },
        secondary: { DEFAULT: '#3B82F6', hover: '#60A5FA', dim: '#3B82F633' },
        dark: { DEFAULT: '#1E40AF' },
        light: { DEFAULT: '#60A5FA' },
        blueAccent: { DEFAULT: '#38BDF8' },
        positive: { DEFAULT: '#22C55E', dim: '#22C55E33' },
        negative: { DEFAULT: '#EF4444', dim: '#EF444433' },
        warning: { DEFAULT: '#F59E0B', dim: '#F59E0B33' },
        text: { DEFAULT: '#F8FAFC', secondary: '#CBD5E1', tertiary: '#64748B' },
      },
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.5s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'ticker': 'ticker 30s linear infinite',
      },
      keyframes: {
        slideIn: { '0%': { transform: 'translateX(-10px)', opacity: '0' }, '100%': { transform: 'translateX(0)', opacity: '1' } },
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        glow: { '0%': { boxShadow: '0 0 5px #2563EB33' }, '100%': { boxShadow: '0 0 20px #2563EB66' } },
        ticker: { '0%': { transform: 'translateX(0)' }, '100%': { transform: 'translateX(-50%)' } },
      },
    },
  },
  plugins: [],
};
export default config;
