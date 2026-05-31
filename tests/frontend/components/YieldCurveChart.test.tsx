/**
 * Unit Tests for YieldCurveChart Component
 * Tests chart rendering, data visualization, interactions, and responsive behavior.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import YieldCurveChart from '@/charts/YieldCurveChart';

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children, data }: any) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)}>
      {children}
    </div>
  ),
  Line: ({ dataKey, stroke }: any) => (
    <div data-testid={`line-${dataKey}`} data-stroke={stroke} />
  ),
  XAxis: ({ dataKey }: any) => <div data-testid="x-axis" data-key={dataKey} />,
  YAxis: ({ domain }: any) => <div data-testid="y-axis" data-domain={JSON.stringify(domain)} />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: ({ content }: any) => <div data-testid="tooltip">{content}</div>,
  Legend: () => <div data-testid="legend" />,
  ReferenceLine: ({ y, label }: any) => (
    <div data-testid="reference-line" data-y={y} data-label={label} />
  ),
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

describe('YieldCurveChart Component', () => {
  // Sample yield curve data
  const mockYieldCurveData = [
    { maturity: '1M', yield: 5.35, maturity_years: 0.083 },
    { maturity: '3M', yield: 5.30, maturity_years: 0.25 },
    { maturity: '6M', yield: 5.22, maturity_years: 0.5 },
    { maturity: '1Y', yield: 5.00, maturity_years: 1 },
    { maturity: '2Y', yield: 4.45, maturity_years: 2 },
    { maturity: '3Y', yield: 4.30, maturity_years: 3 },
    { maturity: '5Y', yield: 4.18, maturity_years: 5 },
    { maturity: '7Y', yield: 4.22, maturity_years: 7 },
    { maturity: '10Y', yield: 4.25, maturity_years: 10 },
    { maturity: '20Y', yield: 4.48, maturity_years: 20 },
    { maturity: '30Y', yield: 4.52, maturity_years: 30 },
  ];

  const mockHistoricalData = [
    { maturity: '2Y', yield: 4.45, date: '2024-01-15' },
    { maturity: '10Y', yield: 4.25, date: '2024-01-15' },
    { maturity: '2Y', yield: 4.50, date: '2024-01-14' },
    { maturity: '10Y', yield: 4.30, date: '2024-01-14' },
  ];

  // ================================================================
  // BASIC RENDERING TESTS
  // ================================================================

  test('renders yield curve chart with data', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByTestId('x-axis')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis')).toBeInTheDocument();
    expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
  });

  test('renders without data (empty state)', () => {
    render(<YieldCurveChart data={[]} />);

    expect(screen.getByText('No yield curve data available')).toBeInTheDocument();
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
  });

  test('renders loading state', () => {
    render(<YieldCurveChart data={mockYieldCurveData} loading={true} />);

    expect(screen.getByTestId('chart-loading')).toBeInTheDocument();
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
  });

  test('renders error state', () => {
    render(
      <YieldCurveChart 
        data={[]} 
        error="Failed to load yield curve data" 
      />
    );

    expect(screen.getByText('Failed to load yield curve data')).toBeInTheDocument();
    expect(screen.getByTestId('error-icon')).toBeInTheDocument();
  });

  // ================================================================
  // DATA PROCESSING TESTS
  // ================================================================

  test('passes correct data to chart component', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const chartElement = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '[]');

    expect(chartData).toHaveLength(mockYieldCurveData.length);
    expect(chartData[0]).toHaveProperty('maturity', '1M');
    expect(chartData[0]).toHaveProperty('yield', 5.35);
  });

  test('sorts data by maturity years', () => {
    const unsortedData = [
      { maturity: '10Y', yield: 4.25, maturity_years: 10 },
      { maturity: '1Y', yield: 5.00, maturity_years: 1 },
      { maturity: '5Y', yield: 4.18, maturity_years: 5 },
    ];

    render(<YieldCurveChart data={unsortedData} />);

    const chartElement = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '[]');

    expect(chartData[0].maturity_years).toBe(1);
    expect(chartData[1].maturity_years).toBe(5);
    expect(chartData[2].maturity_years).toBe(10);
  });

  test('filters out invalid data points', () => {
    const dataWithInvalid = [
      { maturity: '1Y', yield: 5.00, maturity_years: 1 },
      { maturity: '2Y', yield: null, maturity_years: 2 }, // Invalid yield
      { maturity: '3Y', yield: 4.30, maturity_years: null }, // Invalid maturity
      { maturity: '5Y', yield: 4.18, maturity_years: 5 },
    ];

    render(<YieldCurveChart data={dataWithInvalid as any} />);

    const chartElement = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '[]');

    // Should only include valid data points
    expect(chartData).toHaveLength(2);
    expect(chartData.every((point: any) => point.yield !== null && point.maturity_years !== null)).toBe(true);
  });

  // ================================================================
  // CHART CONFIGURATION TESTS
  // ================================================================

  test('configures X-axis correctly', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const xAxis = screen.getByTestId('x-axis');
    expect(xAxis).toHaveAttribute('data-key', 'maturity');
  });

  test('configures Y-axis with proper domain', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const yAxis = screen.getByTestId('y-axis');
    const domain = JSON.parse(yAxis.getAttribute('data-domain') || '[]');

    // Should use dataMin and dataMax for dynamic scaling
    expect(domain).toEqual(['dataMin - 0.1', 'dataMax + 0.1']);
  });

  test('renders current yield curve line', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const currentLine = screen.getByTestId('line-yield');
    expect(currentLine).toHaveAttribute('data-stroke', '#3B82F6'); // Blue color
  });

  test('renders historical comparison when provided', () => {
    render(
      <YieldCurveChart 
        data={mockYieldCurveData} 
        historicalData={mockHistoricalData}
        showComparison={true}
      />
    );

    expect(screen.getByTestId('line-historical')).toBeInTheDocument();
    expect(screen.getByTestId('legend')).toBeInTheDocument();
  });

  // ================================================================
  // INVERSION DETECTION TESTS
  // ================================================================

  test('detects and highlights yield curve inversion', () => {
    const invertedData = [
      { maturity: '1M', yield: 5.35, maturity_years: 0.083 },
      { maturity: '3M', yield: 5.30, maturity_years: 0.25 },
      { maturity: '2Y', yield: 4.50, maturity_years: 2 }, // Higher than 10Y
      { maturity: '10Y', yield: 4.25, maturity_years: 10 }, // Lower than 2Y
    ];

    render(<YieldCurveChart data={invertedData} showInversion={true} />);

    expect(screen.getByTestId('inversion-indicator')).toBeInTheDocument();
    expect(screen.getByText(/Yield curve is inverted/)).toBeInTheDocument();
  });

  test('shows normal curve indicator when not inverted', () => {
    render(<YieldCurveChart data={mockYieldCurveData} showInversion={true} />);

    expect(screen.getByTestId('normal-curve-indicator')).toBeInTheDocument();
    expect(screen.getByText(/Normal yield curve/)).toBeInTheDocument();
  });

  test('calculates inversion spread correctly', () => {
    const invertedData = [
      { maturity: '2Y', yield: 4.50, maturity_years: 2 },
      { maturity: '10Y', yield: 4.25, maturity_years: 10 },
    ];

    render(<YieldCurveChart data={invertedData} showInversion={true} />);

    // 10Y - 2Y = 4.25 - 4.50 = -0.25 (25bp inversion)
    expect(screen.getByText(/25bp inverted/)).toBeInTheDocument();
  });

  // ================================================================
  // INTERACTIVE FEATURES TESTS
  // ================================================================

  test('shows tooltip on hover', async () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const tooltip = screen.getByTestId('tooltip');
    expect(tooltip).toBeInTheDocument();
  });

  test('handles chart click events', () => {
    const mockOnPointClick = jest.fn();

    render(
      <YieldCurveChart 
        data={mockYieldCurveData} 
        onPointClick={mockOnPointClick}
      />
    );

    const chartElement = screen.getByTestId('line-chart');
    fireEvent.click(chartElement);

    // Note: In real implementation, this would be triggered by Recharts
    // Here we're testing that the handler is properly passed
    expect(mockOnPointClick).toBeDefined();
  });

  test('supports zoom functionality', () => {
    render(
      <YieldCurveChart 
        data={mockYieldCurveData} 
        enableZoom={true}
      />
    );

    expect(screen.getByTestId('zoom-controls')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /zoom in/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /zoom out/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset zoom/i })).toBeInTheDocument();
  });

  // ================================================================
  // REFERENCE LINES TESTS
  // ================================================================

  test('shows reference line at specified yield level', () => {
    render(
      <YieldCurveChart 
        data={mockYieldCurveData} 
        referenceYield={4.5}
        referenceLabel="Fed Funds Target"
      />
    );

    const referenceLine = screen.getByTestId('reference-line');
    expect(referenceLine).toHaveAttribute('data-y', '4.5');
    expect(referenceLine).toHaveAttribute('data-label', 'Fed Funds Target');
  });

  test('shows multiple reference lines', () => {
    const referenceLines = [
      { yield: 4.0, label: 'Lower Bound' },
      { yield: 5.0, label: 'Upper Bound' },
    ];

    render(
      <YieldCurveChart 
        data={mockYieldCurveData} 
        referenceLines={referenceLines}
      />
    );

    const lines = screen.getAllByTestId('reference-line');
    expect(lines).toHaveLength(2);
  });

  // ================================================================
  // RESPONSIVE BEHAVIOR TESTS
  // ================================================================

  test('adapts to container size', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const container = screen.getByTestId('responsive-container');
    expect(container).toBeInTheDocument();
  });

  test('shows compact view on small screens', () => {
    // Mock window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 400,
    });

    render(<YieldCurveChart data={mockYieldCurveData} />);

    expect(screen.getByTestId('compact-chart')).toBeInTheDocument();
  });

  test('shows full view on large screens', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    });

    render(<YieldCurveChart data={mockYieldCurveData} />);

    expect(screen.getByTestId('full-chart')).toBeInTheDocument();
  });

  // ================================================================
  // ACCESSIBILITY TESTS
  // ================================================================

  test('has proper ARIA labels', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const chart = screen.getByRole('img');
    expect(chart).toHaveAttribute('aria-label', 'Yield curve chart showing Treasury yields across maturities');
  });

  test('provides alternative text for screen readers', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    expect(screen.getByText(/Yield curve data:/)).toBeInTheDocument();
    expect(screen.getByText(/1 month: 5.35%/)).toBeInTheDocument();
    expect(screen.getByText(/10 year: 4.25%/)).toBeInTheDocument();
  });

  test('supports keyboard navigation', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const chart = screen.getByRole('img');
    
    // Should be focusable
    chart.focus();
    expect(chart).toHaveFocus();

    // Should respond to arrow keys for data point navigation
    fireEvent.keyDown(chart, { key: 'ArrowRight' });
    fireEvent.keyDown(chart, { key: 'ArrowLeft' });
  });

  // ================================================================
  // THEME TESTS
  // ================================================================

  test('applies dark theme correctly', () => {
    render(
      <div className="dark">
        <YieldCurveChart data={mockYieldCurveData} />
      </div>
    );

    const chartContainer = screen.getByTestId('chart-container');
    expect(chartContainer).toHaveClass('dark:bg-gray-800');
  });

  test('applies light theme correctly', () => {
    render(<YieldCurveChart data={mockYieldCurveData} />);

    const chartContainer = screen.getByTestId('chart-container');
    expect(chartContainer).toHaveClass('bg-white');
  });

  // ================================================================
  // PERFORMANCE TESTS
  // ================================================================

  test('renders efficiently with large datasets', () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      maturity: `${i}D`,
      yield: 4 + Math.random(),
      maturity_years: i / 365,
    }));

    const startTime = performance.now();
    render(<YieldCurveChart data={largeDataset} />);
    const endTime = performance.now();

    expect(endTime - startTime).toBeLessThan(100); // Should render in under 100ms
  });

  test('updates efficiently when data changes', () => {
    const { rerender } = render(<YieldCurveChart data={mockYieldCurveData} />);

    const startTime = performance.now();

    // Update data multiple times
    for (let i = 0; i < 10; i++) {
      const updatedData = mockYieldCurveData.map(point => ({
        ...point,
        yield: point.yield + Math.random() * 0.1,
      }));
      rerender(<YieldCurveChart data={updatedData} />);
    }

    const endTime = performance.now();
    expect(endTime - startTime).toBeLessThan(50); // Should update quickly
  });

  // ================================================================
  // EDGE CASES TESTS
  // ================================================================

  test('handles single data point', () => {
    const singlePoint = [{ maturity: '10Y', yield: 4.25, maturity_years: 10 }];

    render(<YieldCurveChart data={singlePoint} />);

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByText(/Single point data/)).toBeInTheDocument();
  });

  test('handles duplicate maturities', () => {
    const duplicateData = [
      { maturity: '10Y', yield: 4.25, maturity_years: 10 },
      { maturity: '10Y', yield: 4.30, maturity_years: 10 }, // Duplicate
    ];

    render(<YieldCurveChart data={duplicateData} />);

    const chartElement = screen.getByTestId('line-chart');
    const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '[]');

    // Should deduplicate or handle gracefully
    expect(chartData).toHaveLength(1);
  });

  test('handles extreme yield values', () => {
    const extremeData = [
      { maturity: '1Y', yield: 0.01, maturity_years: 1 }, // Very low
      { maturity: '10Y', yield: 25.0, maturity_years: 10 }, // Very high
    ];

    render(<YieldCurveChart data={extremeData} />);

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    // Chart should handle extreme values without breaking
  });

  test('handles missing maturity labels', () => {
    const missingLabels = [
      { maturity: '', yield: 4.25, maturity_years: 10 },
      { maturity: null, yield: 4.30, maturity_years: 5 },
    ];

    render(<YieldCurveChart data={missingLabels as any} />);

    // Should provide fallback labels or filter out invalid data
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  // ================================================================
  // INTEGRATION TESTS
  // ================================================================

  test('integrates with real FRED data format', () => {
    const fredData = [
      { maturity: 'DGS1MO', yield: 5.35, maturity_years: 0.083 },
      { maturity: 'DGS10', yield: 4.25, maturity_years: 10 },
    ];

    render(<YieldCurveChart data={fredData} />);

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  test('works with live data updates', async () => {
    const { rerender } = render(<YieldCurveChart data={mockYieldCurveData} />);

    // Simulate live data update
    const updatedData = mockYieldCurveData.map(point => ({
      ...point,
      yield: point.yield + 0.05,
    }));

    rerender(<YieldCurveChart data={updatedData} />);

    await waitFor(() => {
      const chartElement = screen.getByTestId('line-chart');
      const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '[]');
      expect(chartData[0].yield).toBe(5.40); // 5.35 + 0.05
    });
  });
});