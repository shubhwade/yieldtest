/**
 * Unit Tests for MetricCard Component
 * Tests all visual states, interactions, and responsive behavior.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetricCard from '@/components/MetricCard';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  TrendingUp: () => <div data-testid="trending-up-icon">↗</div>,
  TrendingDown: () => <div data-testid="trending-down-icon">↘</div>,
  Minus: () => <div data-testid="minus-icon">-</div>,
  Info: () => <div data-testid="info-icon">i</div>,
}));

describe('MetricCard Component', () => {
  // ================================================================
  // BASIC RENDERING TESTS
  // ================================================================

  test('renders basic metric card with required props', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    expect(screen.getByText('10Y Treasury')).toBeInTheDocument();
    expect(screen.getByText('4.25%')).toBeInTheDocument();
    expect(screen.getByText('-0.03%')).toBeInTheDocument();
  });

  test('renders without change value', () => {
    render(
      <MetricCard
        label="Fed Funds Rate"
        value={5.33}
        unit="%"
      />
    );

    expect(screen.getByText('Fed Funds Rate')).toBeInTheDocument();
    expect(screen.getByText('5.33%')).toBeInTheDocument();
    // Should not show change indicator
    expect(screen.queryByTestId('trending-up-icon')).not.toBeInTheDocument();
    expect(screen.queryByTestId('trending-down-icon')).not.toBeInTheDocument();
  });

  test('renders without unit', () => {
    render(
      <MetricCard
        label="Bond Count"
        value={1250}
        change={50}
      />
    );

    expect(screen.getByText('Bond Count')).toBeInTheDocument();
    expect(screen.getByText('1250')).toBeInTheDocument();
    expect(screen.getByText('+50')).toBeInTheDocument();
  });

  // ================================================================
  // VALUE FORMATTING TESTS
  // ================================================================

  test('formats integer values correctly', () => {
    render(
      <MetricCard
        label="Portfolio Count"
        value={1000}
        unit=""
      />
    );

    expect(screen.getByText('1000')).toBeInTheDocument();
  });

  test('formats decimal values correctly', () => {
    const testCases = [
      { value: 4.25, expected: '4.25' },
      { value: 4.2, expected: '4.20' },
      { value: 4, expected: '4.00' },
      { value: 4.123456, expected: '4.12' },
    ];

    testCases.forEach(({ value, expected }, index) => {
      const { unmount } = render(
        <MetricCard
          key={index}
          label="Test Value"
          value={value}
          unit="%"
        />
      );

      expect(screen.getByText(`${expected}%`)).toBeInTheDocument();
      unmount();
    });
  });

  test('formats large numbers with commas', () => {
    render(
      <MetricCard
        label="Portfolio Value"
        value={1234567.89}
        unit="$"
        prefix="$"
      />
    );

    expect(screen.getByText('$1,234,567.89')).toBeInTheDocument();
  });

  test('formats negative values correctly', () => {
    render(
      <MetricCard
        label="P&L"
        value={-1250.50}
        unit=""
        prefix="$"
      />
    );

    expect(screen.getByText('$-1,250.50')).toBeInTheDocument();
  });

  test('formats very small values correctly', () => {
    render(
      <MetricCard
        label="Spread"
        value={0.001}
        unit="bps"
      />
    );

    expect(screen.getByText('0.00bps')).toBeInTheDocument();
  });

  // ================================================================
  // CHANGE INDICATOR TESTS
  // ================================================================

  test('shows positive change with up arrow and green color', () => {
    render(
      <MetricCard
        label="Yield"
        value={4.25}
        change={0.05}
        unit="%"
      />
    );

    expect(screen.getByTestId('trending-up-icon')).toBeInTheDocument();
    expect(screen.getByText('+0.05%')).toBeInTheDocument();
    
    const changeElement = screen.getByText('+0.05%').parentElement;
    expect(changeElement).toHaveClass('text-green-400');
  });

  test('shows negative change with down arrow and red color', () => {
    render(
      <MetricCard
        label="Yield"
        value={4.25}
        change={-0.05}
        unit="%"
      />
    );

    expect(screen.getByTestId('trending-down-icon')).toBeInTheDocument();
    expect(screen.getByText('-0.05%')).toBeInTheDocument();
    
    const changeElement = screen.getByText('-0.05%').parentElement;
    expect(changeElement).toHaveClass('text-red-400');
  });

  test('shows zero change with minus icon and gray color', () => {
    render(
      <MetricCard
        label="Yield"
        value={4.25}
        change={0}
        unit="%"
      />
    );

    expect(screen.getByTestId('minus-icon')).toBeInTheDocument();
    expect(screen.getByText('0.00%')).toBeInTheDocument();
    
    const changeElement = screen.getByText('0.00%').parentElement;
    expect(changeElement).toHaveClass('text-gray-400');
  });

  test('formats change values correctly', () => {
    const testCases = [
      { change: 0.1, expected: '+0.10%' },
      { change: -0.1, expected: '-0.10%' },
      { change: 0.001, expected: '+0.00%' },
      { change: 1.234, expected: '+1.23%' },
    ];

    testCases.forEach(({ change, expected }, index) => {
      const { unmount } = render(
        <MetricCard
          key={index}
          label="Test"
          value={4.25}
          change={change}
          unit="%"
        />
      );

      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  // ================================================================
  // TOOLTIP TESTS
  // ================================================================

  test('shows tooltip on hover when description provided', async () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        description="Current yield on 10-year U.S. Treasury bonds"
      />
    );

    const card = screen.getByRole('button');
    fireEvent.mouseEnter(card);

    await waitFor(() => {
      expect(screen.getByText('Current yield on 10-year U.S. Treasury bonds')).toBeInTheDocument();
    });
  });

  test('hides tooltip on mouse leave', async () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        description="Current yield on 10-year U.S. Treasury bonds"
      />
    );

    const card = screen.getByRole('button');
    
    // Show tooltip
    fireEvent.mouseEnter(card);
    await waitFor(() => {
      expect(screen.getByText('Current yield on 10-year U.S. Treasury bonds')).toBeInTheDocument();
    });

    // Hide tooltip
    fireEvent.mouseLeave(card);
    await waitFor(() => {
      expect(screen.queryByText('Current yield on 10-year U.S. Treasury bonds')).not.toBeInTheDocument();
    });
  });

  test('does not show tooltip when no description provided', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    const card = screen.getByRole('button');
    fireEvent.mouseEnter(card);

    // Should not show any tooltip
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  // ================================================================
  // CLICK HANDLER TESTS
  // ================================================================

  test('calls onClick handler when clicked', () => {
    const mockOnClick = jest.fn();
    
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        onClick={mockOnClick}
      />
    );

    const card = screen.getByRole('button');
    fireEvent.click(card);

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  test('does not call onClick when not provided', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    const card = screen.getByRole('button');
    fireEvent.click(card);

    // Should not throw error
    expect(card).toBeInTheDocument();
  });

  // ================================================================
  // LOADING STATE TESTS
  // ================================================================

  test('shows loading state correctly', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        loading={true}
      />
    );

    // Should show skeleton/loading animation
    expect(screen.getByTestId('metric-card-loading')).toBeInTheDocument();
  });

  test('shows normal state when not loading', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        loading={false}
      />
    );

    expect(screen.queryByTestId('metric-card-loading')).not.toBeInTheDocument();
    expect(screen.getByText('10Y Treasury')).toBeInTheDocument();
  });

  // ================================================================
  // ERROR STATE TESTS
  // ================================================================

  test('shows error state correctly', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        error="Failed to load data"
      />
    );

    expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    expect(screen.getByTestId('error-icon')).toBeInTheDocument();
  });

  test('shows normal state when no error', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    expect(screen.queryByTestId('error-icon')).not.toBeInTheDocument();
    expect(screen.getByText('10Y Treasury')).toBeInTheDocument();
  });

  // ================================================================
  // ACCESSIBILITY TESTS
  // ================================================================

  test('has proper ARIA labels', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        description="Treasury yield information"
      />
    );

    const card = screen.getByRole('button');
    expect(card).toHaveAttribute('aria-label', '10Y Treasury: 4.25%, down 0.03%');
  });

  test('has proper ARIA description when provided', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        description="Current yield on 10-year U.S. Treasury bonds"
      />
    );

    const card = screen.getByRole('button');
    expect(card).toHaveAttribute('aria-describedby');
  });

  test('supports keyboard navigation', () => {
    const mockOnClick = jest.fn();
    
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        onClick={mockOnClick}
      />
    );

    const card = screen.getByRole('button');
    
    // Should be focusable
    card.focus();
    expect(card).toHaveFocus();

    // Should respond to Enter key
    fireEvent.keyDown(card, { key: 'Enter', code: 'Enter' });
    expect(mockOnClick).toHaveBeenCalledTimes(1);

    // Should respond to Space key
    fireEvent.keyDown(card, { key: ' ', code: 'Space' });
    expect(mockOnClick).toHaveBeenCalledTimes(2);
  });

  // ================================================================
  // RESPONSIVE BEHAVIOR TESTS
  // ================================================================

  test('applies responsive classes correctly', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        size="lg"
      />
    );

    const card = screen.getByText('10Y Treasury').closest('div');
    expect(card).toHaveClass('scale-110');
  });

  test('applies compact size correctly', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        size="sm"
      />
    );

    const card = screen.getByText('10Y Treasury').closest('div');
    expect(card).toHaveClass('scale-90');
  });

  // ================================================================
  // THEME TESTS
  // ================================================================

  test('applies dark theme correctly', () => {
    render(
      <div className="dark">
        <MetricCard
          label="10Y Treasury"
          value={4.25}
          change={-0.03}
          unit="%"
        />
      </div>
    );

    const card = screen.getByRole('button');
    expect(card).toHaveClass('bg-gray-800'); // Dark background
  });

  test('applies light theme correctly', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    const card = screen.getByRole('button');
    expect(card).toHaveClass('bg-white'); // Light background
  });

  // ================================================================
  // EDGE CASES TESTS
  // ================================================================

  test('handles very long labels gracefully', () => {
    const longLabel = 'Very Long Treasury Bond Label That Should Wrap Or Truncate Properly';
    
    render(
      <MetricCard
        label={longLabel}
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    expect(screen.getByText(longLabel)).toBeInTheDocument();
  });

  test('handles zero values correctly', () => {
    render(
      <MetricCard
        label="Zero Value"
        value={0}
        change={0}
        unit="%"
      />
    );

    expect(screen.getByText('0.00%')).toBeInTheDocument();
    expect(screen.getByText('0.00%')).toBeInTheDocument(); // Change also shows as 0.00%
  });

  test('handles null/undefined values gracefully', () => {
    render(
      <MetricCard
        label="Missing Data"
        value={null as any}
        change={undefined as any}
        unit="%"
      />
    );

    expect(screen.getByText('Missing Data')).toBeInTheDocument();
    expect(screen.getByText('--')).toBeInTheDocument(); // Should show placeholder
  });

  test('handles extremely large numbers', () => {
    render(
      <MetricCard
        label="Large Number"
        value={999999999.99}
        change={1000000}
        unit=""
      />
    );

    expect(screen.getByText('999,999,999.99')).toBeInTheDocument();
    expect(screen.getByText('+1,000,000.00')).toBeInTheDocument();
  });

  test('handles extremely small numbers', () => {
    render(
      <MetricCard
        label="Small Number"
        value={0.000001}
        change={-0.000001}
        unit="bps"
      />
    );

    expect(screen.getByText('0.00bps')).toBeInTheDocument(); // Rounds to display precision
  });

  // ================================================================
  // ANIMATION TESTS
  // ================================================================

  test('applies hover animation classes', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
        onClick={() => {}}
      />
    );

    const card = screen.getByRole('button');
    expect(card).toHaveClass('hover:scale-105'); // Hover scale animation
  });

  test('applies transition classes', () => {
    render(
      <MetricCard
        label="10Y Treasury"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    const card = screen.getByRole('button');
    expect(card).toHaveClass('transition-all'); // Smooth transitions
  });

  // ================================================================
  // INTEGRATION TESTS
  // ================================================================

  test('works correctly with real market data format', () => {
    const marketData = {
      label: '10Y Treasury',
      value: 4.2534,
      change: -0.0287,
      unit: '%',
      description: 'Current yield on 10-year U.S. Treasury bonds',
    };

    render(<MetricCard {...marketData} />);

    expect(screen.getByText('10Y Treasury')).toBeInTheDocument();
    expect(screen.getByText('4.25%')).toBeInTheDocument();
    expect(screen.getByText('-0.03%')).toBeInTheDocument();
  });

  test('works correctly in grid layout', () => {
    render(
      <div className="grid grid-cols-3 gap-4">
        <MetricCard label="2Y" value={4.45} change={0.05} unit="%" />
        <MetricCard label="10Y" value={4.25} change={-0.03} unit="%" />
        <MetricCard label="30Y" value={4.52} change={-0.02} unit="%" />
      </div>
    );

    expect(screen.getByText('2Y')).toBeInTheDocument();
    expect(screen.getByText('10Y')).toBeInTheDocument();
    expect(screen.getByText('30Y')).toBeInTheDocument();
  });
});

// ================================================================
// PERFORMANCE TESTS
// ================================================================

describe('MetricCard Performance', () => {
  test('renders quickly with many instances', () => {
    const startTime = performance.now();

    const cards = Array.from({ length: 100 }, (_, i) => (
      <MetricCard
        key={i}
        label={`Metric ${i}`}
        value={Math.random() * 10}
        change={(Math.random() - 0.5) * 0.1}
        unit="%"
      />
    ));

    render(<div>{cards}</div>);

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render 100 cards in under 100ms
    expect(renderTime).toBeLessThan(100);
  });

  test('updates efficiently when props change', () => {
    const { rerender } = render(
      <MetricCard
        label="Test"
        value={4.25}
        change={-0.03}
        unit="%"
      />
    );

    const startTime = performance.now();

    // Update props multiple times
    for (let i = 0; i < 50; i++) {
      rerender(
        <MetricCard
          label="Test"
          value={4.25 + i * 0.01}
          change={-0.03 + i * 0.001}
          unit="%"
        />
      );
    }

    const endTime = performance.now();
    const updateTime = endTime - startTime;

    // Should update 50 times in under 50ms
    expect(updateTime).toBeLessThan(50);
  });
});