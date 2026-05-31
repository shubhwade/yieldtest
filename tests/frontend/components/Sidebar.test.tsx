import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '@/layouts/Sidebar';
import { usePathname } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    aside: ({ children, ...props }: any) => <aside {...props}>{children}</aside>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('Sidebar Component', () => {
  const mockOnToggle = jest.fn();

  beforeEach(() => {
    (usePathname as jest.Mock).mockReturnValue('/dashboard');
  });

  it('renders the logo and application name', () => {
    render(<Sidebar collapsed={false} onToggle={mockOnToggle} />);
    expect(screen.getByText('YIELD')).toBeInTheDocument();
    expect(screen.getByText('LENS')).toBeInTheDocument();
    expect(screen.getByText('Fixed Income Intelligence')).toBeInTheDocument();
  });

  it('renders navigation items', () => {
    render(<Sidebar collapsed={false} onToggle={mockOnToggle} />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Bond Screener')).toBeInTheDocument();
    expect(screen.getByText('Yield Analytics')).toBeInTheDocument();
  });

  it('highlights the active route', () => {
    (usePathname as jest.Mock).mockReturnValue('/screener');
    render(<Sidebar collapsed={false} onToggle={mockOnToggle} />);
    
    // The active link should have specific classes
    const screenerLink = screen.getByText('Bond Screener').closest('div');
    expect(screenerLink).toHaveClass('bg-accent/10');
    expect(screenerLink).toHaveClass('text-accent');
  });

  it('hides labels when collapsed', () => {
    render(<Sidebar collapsed={true} onToggle={mockOnToggle} />);
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('Fixed Income Intelligence')).not.toBeInTheDocument();
  });

  it('calls onToggle when collapse button is clicked', () => {
    render(<Sidebar collapsed={false} onToggle={mockOnToggle} />);
    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);
    expect(mockOnToggle).toHaveBeenCalledTimes(1);
  });
});
