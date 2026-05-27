import { test, expect } from '@playwright/test';

test.describe('YieldLens UI Exhaustive Validation', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
  });

  test.describe('Logo & Branding', () => {
    test('Logo should be visible in the top left of the sidebar', async ({ page }) => {
      const logo = page.locator('aside >> text=YIELDLENS');
      await expect(logo).toBeVisible();
      
      const logoIcon = page.locator('aside >> .lucide-zap');
      await expect(logoIcon).toBeVisible();
    });

    test('Logo should load instantly and stay fixed', async ({ page }) => {
      const logoContainer = page.locator('aside >> div').first();
      await expect(logoContainer).toBeVisible();
      // Check if it's fixed (should stay in viewport even after scroll)
      await page.evaluate(() => window.scrollTo(0, 1000));
      await expect(logoContainer).toBeInViewport();
    });

    test('Logo should be responsive on different viewports', async ({ page }) => {
      // Mobile view (sidebar usually collapses or hides)
      await page.setViewportSize({ width: 375, height: 667 });
      // In mobile, sidebar might be hidden or collapsed
      // Our Sidebar.tsx uses motion.aside animate width 64
      const sidebar = page.locator('aside');
      const box = await sidebar.boundingBox();
      expect(box?.width).toBe(64);
      
      // Desktop view
      await page.setViewportSize({ width: 1920, height: 1080 });
      const expandedBox = await sidebar.boundingBox();
      // If it's expanded by default or after toggle
      // The component starts with collapsed=false in AppShell.tsx
      expect(expandedBox?.width).toBe(240);
    });
  });

  test.describe('Sidebar Navigation', () => {
    const navItems = [
      { label: 'Dashboard', href: '/dashboard' },
      { label: 'Markets', href: '/markets' },
      { label: 'Bond Screener', href: '/screener' },
      { label: 'FI Comparison', href: '/comparison' },
      { label: 'Yield Analytics', href: '/analytics' },
      { label: 'Treasury Curve', href: '/treasury' },
      { label: 'Credit Analysis', href: '/credit' },
      { label: 'Macro Dashboard', href: '/macro' },
      { label: 'Portfolio', href: '/portfolio' },
      { label: 'Watchlist', href: '/watchlist' },
      { label: 'AI Insights', href: '/ai' },
      { label: 'News', href: '/news' },
      { label: 'Settings', href: '/settings' },
    ];

    for (const item of navItems) {
      test(`Should navigate to ${item.label}`, async ({ page }) => {
        await page.click(`aside >> text=${item.label}`);
        await expect(page).toHaveURL(item.href);
        // Check active state in sidebar
        const activeLink = page.locator(`aside >> a[href="${item.href}"] >> div`);
        await expect(activeLink).toHaveClass(/bg-accent\/10/);
      });
    }

    test('Sidebar should collapse and expand', async ({ page }) => {
      const toggleBtn = page.locator('aside >> button');
      
      // Collapse
      await toggleBtn.click();
      const sidebar = page.locator('aside');
      await expect(sidebar).toHaveCSS('width', '64px');
      
      // Labels should be hidden
      const label = page.locator('aside >> text=Dashboard');
      await expect(label).not.toBeVisible();
      
      // Expand
      await toggleBtn.click();
      await expect(sidebar).toHaveCSS('width', '240px');
      await expect(label).toBeVisible();
    });
  });

  test.describe('Dashboard Components', () => {
    test('Treasury cards should load with data', async ({ page }) => {
      const treasurySection = page.locator('text=Treasury Yield Curve');
      await expect(treasurySection).toBeVisible();
      
      const cards = page.locator('.panel >> .metric-value');
      const count = await cards.count();
      expect(count).toBeGreaterThan(0);
      
      // Verify no "N/A" or missing values
      const firstCardValue = await cards.first().textContent();
      expect(firstCardValue).not.toBe('N/A');
      expect(firstCardValue).toMatch(/\d+\.\d+%/);
    });

    test('Heatmaps and Charts should render', async ({ page }) => {
      const heatmap = page.locator('text=Yield Heatmap');
      await expect(heatmap).toBeVisible();
      
      // Recharts should render SVG
      const chart = page.locator('.recharts-surface');
      await expect(chart).toBeVisible();
    });

    test('AI Summary should load', async ({ page }) => {
      const aiBrief = page.locator('text=AI Daily Brief');
      await expect(aiBrief).toBeVisible();
      
      const briefContent = page.locator('.panel:has-text("AI Daily Brief") >> .panel-body');
      await expect(briefContent).not.toBeEmpty();
    });
  });

  test.describe('Bond Screener Filters', () => {
    test('Should apply filters and update results', async ({ page }) => {
      await page.goto('/screener');
      
      // Select a filter (e.g., Corporate)
      const corporateFilter = page.locator('button:has-text("Corporate")');
      if (await corporateFilter.isVisible()) {
        await corporateFilter.click();
        // Wait for results to update
        await page.waitForResponse(response => response.url().includes('/screener/search') && response.status() === 200);
      }
      
      const tableRows = page.locator('.table-row');
      expect(await tableRows.count()).toBeGreaterThan(0);
    });
  });

  test.describe('Responsive Design', () => {
    test('Layout should adjust for mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Sidebar should be collapsed
      const sidebar = page.locator('aside');
      await expect(sidebar).toHaveCSS('width', '64px');
      
      // Main content should be visible
      const main = page.locator('main');
      await expect(main).toBeVisible();
    });
  });
});
