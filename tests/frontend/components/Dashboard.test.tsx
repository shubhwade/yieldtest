import React from 'react';
import { render, screen } from '@testing-library/react';
import Dashboard from '@/app/dashboard/page';

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  LayoutDashboard: () => <div data-testid="icon-dashboard" />,
  TrendingUp: () => <div data-testid="icon-up" />,
  TrendingDown: () => <div data-testid="icon-down" />,
  Activity: () => <div data-testid="icon-activity" />,
  Brain: () => <div data-testid="icon-brain" />,
  Eye: () => <div data-testid="icon-eye" />,
  Bell: () => <div data-testid="icon-bell" />,
  Zap: () => <div data-testid="icon-zap" />,
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// Mock Recharts to avoid SVG rendering issues in JSDOM
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  AreaChart: () => <div data-testid="chart-area" />,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

describe('Dashboard Page', () => {
  it('renders all main sections', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Treasury Yield Curve')).toBeInTheDocument();
    expect(screen.getByText('Yield Heatmap')).toBeInTheDocument();
    expect(screen.getByText('AI Daily Brief')).toBeInTheDocument();
    expect(screen.getByText('Top Movers')).toBeInTheDocument();
    expect(screen.getByText('Watchlist')).toBeInTheDocument();
  });

  it('renders treasury yield cards with correct formatting', () => {
    render(<Dashboard />);
    // Check for some mock values (e.g., 1M, 2Y, 10Y)
    expect(screen.getByText('1M')).toBeInTheDocument();
    expect(screen.getByText('10Y')).toBeInTheDocument();
    expect(screen.getByText('30Y')).toBeInTheDocument();
  });

  it('renders AI Daily Brief with Gemini badge', () => {
    render(<Dashboard />);
    expect(screen.getByText('Gemini')).toBeInTheDocument();
    expect(screen.getByTestId('icon-brain')).toBeInTheDocument();
  });
});
